"""Account endpoints — thin wrappers around dj-rest-auth's registration view.

Adds:
- Per-IP rate limiting (Story 1.3 §AC6 — 5/hour).
- Generic-message response on duplicate emails (CWE-203 user enumeration prevention).
- A `csrf` endpoint the front calls on mount to seed its CSRF cookie before any POST.

Structured signup logging is wired in `apps.accounts.signals` on allauth's `user_signed_up`
signal, so the view itself does not need to know about the freshly-created user.

Duplicate-email detection runs at the serializer level (`SignupSerializer.validate`); the
narrow `IntegrityError` catch below is a backstop for the TOCTOU race between the
`exists()` check and the eventual DB insert.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from dateutil.relativedelta import relativedelta
from dj_rest_auth.registration.views import RegisterView, ResendEmailVerificationView
from dj_rest_auth.views import LoginView, PasswordResetConfirmView, PasswordResetView
from django.conf import settings
from django.db import IntegrityError
from django.db.models import F
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework import status as drf_status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.accounts.gdpr_exceptions import (
    AccountDeleted,
    AccountDeletionNoPending,
    AccountDeletionNotFound,
    AccountLocked,
    AccountSuspended,
    EmailNotVerified,
    GdprExportDownloadCap,
    GdprExportExpired,
    GdprExportNotReady,
)
from apps.accounts.models import (
    STAFF_ROLES_REQUIRING_MFA,
    AccountDeletionRequest,
    GdprExportRequest,
    GdprExportStatus,
    ParentalConsent,
)
from apps.accounts.serializers import (
    AccountDeletionCancelPayloadSerializer,
    AccountDeletionPublicStatusSerializer,
    AccountDeletionRequestPayloadSerializer,
    AccountDeletionRequestSerializer,
    GdprExportRequestSerializer,
    ParentalConsentDecisionSerializer,
    ParentalConsentStatusSerializer,
)
from apps.accounts.services import account_deletion as account_deletion_service
from apps.accounts.services.gdpr_service import (
    GdprExportService,
    gdpr_s3_client,
)
from apps.accounts.services.parental_consent import record_decision
from apps.accounts.services.parental_consent_email import (
    send_granted_to_child,
    send_reminder_to_parent,
)
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.exceptions import (
    EmailAlreadyRegistered,
    ParentalConsentNotFound,
    RateLimited,
)
from apps.core.rls import bypass_rls
from apps.core.text import mask_email


class _CsrfResponseSerializer(serializers.Serializer):
    """Drf-spectacular schema for /auth/csrf/."""

    csrf_token = serializers.CharField()


@extend_schema(
    summary="Bootstrap CSRF cookie",
    description=(
        "Seeds the `csrftoken` cookie so the SPA can include `X-CSRFToken` on subsequent "
        "POST/PUT/DELETE requests. Call once on mount."
    ),
    responses={200: _CsrfResponseSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request: Request) -> Response:
    return Response({"csrf_token": get_token(request._request)})


@method_decorator(ratelimit(key="ip", rate="5/h", block=False), name="dispatch")
class ThrottledRegisterView(RegisterView):
    """Signup endpoint — wraps dj-rest-auth's RegisterView with rate limiting + IntegrityError narrowing."""

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if getattr(request, "limited", False):
            raise RateLimited(retry_after_seconds=3600)
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as exc:
            # TOCTOU race: two concurrent signups both pass `SignupSerializer.validate`'s
            # `.exists()` check, then collide at the DB unique constraint. Translate the
            # raw IntegrityError into the same generic Problem we already return at the
            # serializer level, so the public response is uniform regardless of which
            # branch caught the duplicate.
            raise EmailAlreadyRegistered() from exc


def _hash_email_for_audit(email: str | None) -> str | None:
    """Lowercase SHA-256 hex of the (normalised) email — Story 1.5 §AC2.

    The audit log keeps `email_hashed` instead of the raw email so the 3-year
    retention doesn't accumulate PII that should never have been there.
    Mirrors the `parent_email_hash` convention from Story 1.4.
    """
    if not email:
        return None
    import hashlib

    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


@method_decorator(ratelimit(key="ip", rate="5/m", block=False), name="dispatch")
class ThrottledLoginView(LoginView):
    """Login endpoint with per-IP throttle (Story 1.12 §D5) + audit hooks (Story 1.5 §AC9).

    The custom `PathAdvisorLoginSerializer` deliberately leaks the DELETED
    user state via a typed 403 (so the front can route to the cancel-flow
    info page). To keep that leak from being exploited as an enumeration
    oracle, this view caps login attempts at 5/min/IP.

    Story 1.5 layers audit-row writes for every login outcome so the DPO can
    answer "was this user's account hammered? when did they last log in
    successfully? was the lockout tripped from one IP or many?".
    """

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            # IP-throttle hit — the user-account-level audit happens elsewhere;
            # log a single structured event here for ops visibility.
            raise RateLimited(retry_after_seconds=60)

        email = (
            (request.data.get("email") or "").strip().lower() if hasattr(request, "data") else None
        )
        ip_truncated = _truncate_ip_for_audit(_client_ip_from_request(request))
        user_agent = (request.headers.get("user-agent") or "")[:200] or None

        try:
            response = super().post(request, *args, **kwargs)
        except AccountLocked:
            # User was ALREADY locked when they tried — distinct from the
            # `auth.account_locked` event that fires once on lockout trip
            # (written by `login_security.record_failed_attempt`).
            _write_login_audit(
                action="auth.login_blocked_locked",
                result=AuditResult.FAILURE,
                email=email,
                ip_truncated=ip_truncated,
                user_agent=user_agent,
            )
            raise
        except (AccountDeleted, AccountSuspended, EmailNotVerified) as exc:
            _write_login_audit(
                action="auth.login_failed",
                result=AuditResult.FAILURE,
                email=email,
                ip_truncated=ip_truncated,
                user_agent=user_agent,
                reason=exc.__class__.__name__,
            )
            raise
        except ValidationError:
            # Wrong password OR unknown email — both produce the same generic
            # 400 body upstream. We differentiate in the audit metadata via
            # `reason` ("invalid_credentials" vs "unknown_email") so the DPO
            # can spot enumeration patterns without changing the public shape.
            # `_write_login_audit` overrides reason → "unknown_email" when
            # the email does not match a known user (subject_id is None).
            _write_login_audit(
                action="auth.login_failed",
                result=AuditResult.FAILURE,
                email=email,
                ip_truncated=ip_truncated,
                user_agent=user_agent,
                reason="invalid_credentials",
            )
            raise

        # Success path — write `auth.login_succeeded` with the actual user id.
        # `self.user` is populated by dj-rest-auth's `LoginView.login()`
        # method as the authenticated user (the serializer puts the User
        # row at `validated_data['user']` and the view promotes it). We
        # prefer it over `request.user` because the latter is still
        # AnonymousUser at this point — the session-auth middleware that
        # would have populated `request.user` only fires on the NEXT
        # request that carries the freshly-issued session cookie.
        user = getattr(self, "user", None)
        user_id = getattr(user, "id", None) if user else None

        # Story 1.6 — MFA gate. If this user requires MFA (staff role OR
        # already-enrolled B2C), the login is NOT complete: we strip the
        # session cookie the parent set, mint an `mfa_session` token, and
        # return a 200 telling the frontend to route through the MFA flow.
        # The audit row records that the PASSWORD leg succeeded but MFA is
        # still pending (metadata.mfa_pending=true).
        requires_mfa = user is not None and user.requires_mfa
        needs_enrollment = False
        if user is not None and requires_mfa:
            # P24 — explicit catch of MfaProfile.DoesNotExist instead of
            # nested `getattr(..., None)` chain that doesn't catch related-
            # object descriptor exceptions reliably across Django versions.
            from apps.accounts.models import MfaProfile as _MfaProfile

            try:
                _profile = user.mfa_profile
                _force_re_enroll = _profile.requires_enrollment_at_next_login
            except _MfaProfile.DoesNotExist:
                _force_re_enroll = False
            needs_enrollment = (not user.has_mfa_enrolled) or _force_re_enroll

        record_audit(
            action="auth.login_succeeded",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user_id,
            metadata={
                "email_hashed": _hash_email_for_audit(email),
                "ip_truncated": ip_truncated,
                "user_agent": user_agent,
                "mfa_pending": bool(requires_mfa),
            },
        )

        if requires_mfa and user is not None:
            from apps.accounts.services import mfa_session as _mfa_session

            stage = "mfa_enrollment_pending" if needs_enrollment else "mfa_pending"
            mfa_token = _mfa_session.issue(
                user=user, stage=stage, ip=_client_ip_from_request(request)
            )

            # Login is NOT complete yet — the parent's `super().post()` called
            # `django.contrib.auth.login()` which wrote to `request.session`,
            # which would cause `SessionMiddleware` to emit a `sessionid`
            # cookie after this view returns. We MUST flush the session so
            # no auth cookie ships back to the client (the MFA challenge
            # endpoint will re-login the user via `django_login(request, user)`
            # only after the TOTP code is verified).
            request.session.flush()
            response.cookies.clear()

            # Code-review D5 — scrub the half-login response to the minimal
            # set of fields the frontend needs to route. The full profile
            # (email, recovery code count, etc.) ships only AFTER the MFA
            # challenge completes; otherwise an attacker with the password
            # but no second factor can probe the victim's profile state
            # (recovery-codes-remaining, etc.) via a single half-login.
            new_payload = {
                "mfa_required": True,
                "mfa_enrollment_required": bool(needs_enrollment),
                "mfa_session": mfa_token,
                "user": _mfa_minimal_user(user),
            }
            return Response(new_payload, status=drf_status.HTTP_200_OK)

        # Non-MFA happy path (B2C non-enrolé). NOW we clear the lockout
        # because the login is fully complete (code-review note: Story 1.5
        # used to clear in the serializer; Story 1.6 moved it here to keep
        # MFA users from resetting the counter on password-only success).
        if user is not None:
            from apps.accounts.services import login_security as _login_security

            _login_security.clear_failed_attempts(user=user, trigger="successful_login")

        # dj-rest-auth returns 204 NoContent in our (session-cookie, no-JWT,
        # no-Token) config. Story 1.5 §AC1 expects 200 + `{"user": {...}}` so
        # the front can drive role-based redirect (§AC8) without a follow-up
        # `/auth/user/` round-trip.
        if response.status_code == 204 and user is not None:
            from apps.accounts.serializers import UserDetailsSerializer

            payload = {"user": UserDetailsSerializer(user).data}
            new_response = Response(payload, status=drf_status.HTTP_200_OK)
            # Preserve every cookie the parent set, attribute-by-attribute.
            # Direct `new_response.cookies[k] = source_morsel` would copy
            # the value but Python's http.cookies SimpleCookie semantics on
            # Morsel-to-Morsel assignment are implementation-dependent (we've
            # been bitten before by silent loss of Secure/HttpOnly/SameSite).
            # Explicit set_cookie() reads the attrs off the source Morsel
            # and re-emits them so the session cookie's security flags are
            # never silently stripped (code-review P16 — Story 1.5 review
            # 2026-05-27).
            for cookie_name, morsel in response.cookies.items():
                new_response.set_cookie(
                    cookie_name,
                    morsel.value,
                    max_age=int(morsel["max-age"]) if morsel["max-age"] else None,
                    expires=morsel["expires"] or None,
                    path=morsel["path"] or "/",
                    domain=morsel["domain"] or None,
                    secure=bool(morsel["secure"]),
                    httponly=bool(morsel["httponly"]),
                    samesite=morsel["samesite"] or None,
                )
            return new_response
        return response


def _write_login_audit(
    *,
    action: str,
    result: str,
    email: str | None,
    ip_truncated: str | None,
    user_agent: str | None,
    reason: str | None = None,
) -> None:
    """Write a login-flow audit row. Resolves `subject_id` from the email
    lookup if the user exists (kept in DB), otherwise leaves it NULL — never
    exposes the "user exists?" signal via HTTP, only via the (DPO-only)
    audit log.
    """
    from apps.accounts.models import User as _User

    subject_id: str | None = None
    if email:
        candidate = _User.objects.filter(email__iexact=email).only("id").first()
        if candidate is not None:
            subject_id = candidate.id

    metadata = {
        "email_hashed": _hash_email_for_audit(email),
        "ip_truncated": ip_truncated,
        "user_agent": user_agent,
    }
    if reason:
        metadata["reason"] = reason
    if not subject_id and email:
        # Internal-only signal for DPO enumeration detection (Story 1.5 §AC2).
        # NEVER reflected in the HTTP response.
        metadata["reason"] = "unknown_email"

    record_audit(
        action=action,
        result=result,
        actor=None,
        subject_id=subject_id,
        metadata=metadata,
    )


def _truncate_ip_for_audit(ip: str | None) -> str | None:
    """Coarsen IPv4 to /24 and IPv6 to /48 — Story 1.5 inlines the helper
    rather than importing from `apps.accounts.services.account_deletion`
    (private function with leading underscore). The duplication is flagged
    in deferred-work for consolidation into `apps/core/text.py`.
    """
    import ipaddress

    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return None
    if isinstance(addr, ipaddress.IPv4Address):
        return str(ipaddress.ip_network(f"{addr}/24", strict=False).network_address)
    return str(ipaddress.ip_network(f"{addr}/48", strict=False).network_address)


def _ratelimit_key_by_email_in_body(group, request) -> str:
    """Per-email rate-limit key for password-reset request endpoint (Story 1.5 §AC5).

    Read directly from `request.body` because django-ratelimit's
    `@method_decorator` runs at `dispatch` time — BEFORE DRF parses the
    request and attaches `request.data`. Reading `request.data` here would
    silently collapse to the empty key on every call (caught code-review
    P1 — Story 1.5 review 2026-05-27).

    Defensive: a request with no body, non-JSON body, or unparseable body
    collapses to the empty key — those still hit the per-IP cap above us.
    """
    import json

    try:
        raw = request.body or b"{}"
        payload = json.loads(raw)
        email = payload.get("email", "") if isinstance(payload, dict) else ""
    except (json.JSONDecodeError, ValueError, AttributeError):
        email = ""
    return (email or "").strip().lower()


@method_decorator(ratelimit(key="ip", rate="5/h", block=False), name="dispatch")
@method_decorator(
    ratelimit(key=_ratelimit_key_by_email_in_body, rate="1/h", block=False),
    name="dispatch",
)
class ThrottledPasswordResetView(PasswordResetView):
    """Password reset request — Story 1.5 §AC5.

    Stacked rate-limits:
    - 5/h per IP: cheap noise blunting (django-ratelimit's IP key).
    - 1/h per submitted email: stops a single legitimate user typing the
      wrong email + resubmitting from clogging the SMTP queue.

    Audit: every successful POST (200) writes either
    `auth.password_reset_requested` (subject_id set) or
    `auth.password_reset_requested_unknown` (subject_id null). The 200
    response body is identical in both branches — the differentiation lives
    in the audit log only (no enumeration leak).
    """

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            raise RateLimited(retry_after_seconds=3600)

        email = (
            (request.data.get("email") or "").strip().lower() if hasattr(request, "data") else ""
        )
        ip_truncated = _truncate_ip_for_audit(_client_ip_from_request(request))

        # Resolve subject BEFORE delegating so we can branch the audit row
        # regardless of whether the user exists. `super().post()` returns
        # 200 in BOTH cases (allauth's PasswordResetForm silently no-ops
        # for unknown emails — same anti-enumeration shape we want).
        from apps.accounts.models import User as _User

        subject_id: str | None = None
        if email:
            candidate = _User.objects.filter(email__iexact=email).only("id").first()
            if candidate is not None:
                subject_id = candidate.id

        response = super().post(request, *args, **kwargs)

        record_audit(
            action=(
                "auth.password_reset_requested"
                if subject_id
                else "auth.password_reset_requested_unknown"
            ),
            result=AuditResult.SUCCESS,
            actor=None,
            subject_id=subject_id,
            metadata={
                "email_hashed": _hash_email_for_audit(email),
                "ip_truncated": ip_truncated,
            },
        )

        # Override the dj-rest-auth default detail with the spec §AC5 wording.
        # AC5's anti-enum contract hinges on the response BODY being identical
        # whether the email is known or unknown — dj-rest-auth's translated
        # default ("Un e-mail de réinitialisation…") doesn't match either
        # branch's expectations. Force the FR copy here (code-review P13 —
        # Story 1.5 review 2026-05-27).
        if response.status_code == 200:
            response.data = {
                "detail": "Si cet email existe, un lien de réinitialisation t'a été envoyé."
            }
        return response


@method_decorator(ratelimit(key="ip", rate="10/h", block=False), name="dispatch")
class ThrottledPasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset confirm — Story 1.5 §AC6.

    On a successful `200` (the parent updates the user's password hash
    inside its own transaction), we:
    - Clear the failed-attempts counter + `locked_until` column so a
      previously-locked user can log in immediately with the new password.
    - Purge every active Django session for the user (a leaked session
      cookie tied to the old password is invalidated atomically).
    - Send a "password changed" confirmation email so the legitimate user
      sees a notification + has a clear "if this wasn't you, contact the
      DPO" escape hatch.
    - Audit-log `auth.password_reset_completed` with `subject_id = user.id`.

    The parent serializer's `PasswordResetConfirmSerializer.save()` resolves
    `self.user` from the uid+token validation — we re-resolve from
    `serializer.user` to plumb the post-save side-effects.
    """

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            raise RateLimited(retry_after_seconds=3600)

        # Defense-in-depth: refuse confirm for DELETED users BEFORE the
        # parent serializer writes the new password hash. The request
        # endpoint already filters on `is_active=True` via allauth's
        # `PasswordResetForm.get_users()` — so a DELETED user should never
        # have a valid token in the first place. This guards against the
        # narrow window where (a) a user was DELETED between request and
        # confirm, or (b) a future migration flips `is_active=True` back on
        # a DELETED row (code-review D4 — Story 1.5 review 2026-05-27).
        # The response body matches allauth's generic invalid-token 400 so
        # the rejection is indistinguishable from an expired/forged token.
        from allauth.account.utils import url_str_to_user_pk

        from apps.accounts.models import User as _User
        from apps.accounts.models import UserStatus as _UserStatus

        uid_in = request.data.get("uid", "") if hasattr(request, "data") else ""
        if uid_in:
            try:
                _pk = url_str_to_user_pk(uid_in)
                _candidate = (
                    _User.objects.filter(pk=_pk).only("id", "status").first() if _pk else None
                )
            except Exception:
                _candidate = None
            if _candidate is not None and _candidate.status == _UserStatus.DELETED:
                return Response(
                    {"token": ["Invalid value"]},
                    status=drf_status.HTTP_400_BAD_REQUEST,
                )

        response = super().post(request, *args, **kwargs)

        # Only run side-effects on a successful reset (HTTP 200). The parent
        # returns 400 + `{"token": ["Invalid value"]}` on expired/invalid
        # tokens, which we leave untouched.
        if response.status_code != 200:
            return response

        # Re-resolve the user from the uid in the POST body — the parent
        # serializer doesn't expose the resolved user via the response.
        # IMPORTANT: with `allauth` in INSTALLED_APPS, dj-rest-auth uses
        # allauth's `user_pk_to_url_str` encoder. Django's stdlib base64
        # decoder produces a different value, so using it here would always
        # fail to resolve.
        #
        # We do NOT re-verify the token here: `PasswordResetTokenGenerator`
        # hashes the user's current password into the token, so by the time
        # `super().post()` returned 200 (password updated), the original
        # token no longer validates. The parent already verified it BEFORE
        # writing the new password — that's the trust boundary we lean on.
        from allauth.account.utils import url_str_to_user_pk

        from apps.accounts.models import User as _User
        from apps.accounts.services import login_security
        from apps.accounts.services.session_utils import terminate_user_sessions

        uid = request.data.get("uid", "")
        ip_truncated = _truncate_ip_for_audit(_client_ip_from_request(request))

        try:
            pk = url_str_to_user_pk(uid)
            user = _User.objects.filter(pk=pk).first()
        except Exception:
            user = None

        # Defensive: if the parent succeeded but we can't resolve the user,
        # don't crash the response. Just log + return — the password IS
        # already updated by the parent's `serializer.save()`.
        if user is None:
            import structlog

            structlog.get_logger(__name__).warning(
                "auth.password_reset_completed.user_unresolved",
                uid_prefix=uid[:8] if uid else None,
            )
            return response

        login_security.clear_failed_attempts(user=user, trigger="password_reset")
        sessions_killed = terminate_user_sessions(user)

        # Confirmation email — best-effort, swallow SMTP errors so the
        # caller still gets the 200 (the password change ITSELF already
        # committed; the notification is a UX nicety). The success/failure
        # is captured in the audit metadata so the DPO can investigate
        # "user claims they were never notified" support tickets
        # (code-review P10 — Story 1.5 review 2026-05-27).
        email_sent = False
        try:
            from allauth.account.adapter import get_adapter

            get_adapter(request).send_mail(
                "account/email/password_reset_completed",
                user.email,
                {"user": user},
            )
            email_sent = True
        except Exception:
            import structlog

            structlog.get_logger(__name__).warning(
                "auth.password_reset_completed.notify_failed",
                user_id=user.id,
                exc_info=True,
            )

        # Actor is None — the confirm endpoint is reached anonymously (the
        # user is not logged in at this point; they just clicked a link from
        # their inbox). Attributing actor=user would misrepresent agency: it
        # could be the legit user OR someone who phished the reset link. The
        # audit row's subject_id captures whose password changed (code-review
        # P5 — Story 1.5 review 2026-05-27).
        record_audit(
            action="auth.password_reset_completed",
            result=AuditResult.SUCCESS,
            actor=None,
            subject_id=user.id,
            metadata={
                "sessions_killed": sessions_killed,
                "email_sent": email_sent,
                "ip_truncated": ip_truncated,
            },
        )

        # Override the dj-rest-auth default detail with the spec §AC6 wording
        # (code-review P13 — Story 1.5 review 2026-05-27).
        response.data = {"detail": "Ton mot de passe a été réinitialisé."}
        return response


@method_decorator(ratelimit(key="ip", rate="5/h", block=False), name="dispatch")
class ThrottledResendEmailView(ResendEmailVerificationView):
    """Resend-email endpoint — wraps dj-rest-auth's view with the same IP throttle.

    Without this wrapper, an attacker could bypass the signup rate limit by repeatedly
    requesting verification-email resends, flooding our SMTP relay and the user's inbox
    (cf. code review §11 patch — abuse vector identified by Edge Case Hunter).
    """

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if getattr(request, "limited", False):
            raise RateLimited(retry_after_seconds=3600)
        return super().create(request, *args, **kwargs)


class _GdprExportCreateThrottle(UserRateThrottle):
    """Defense-in-depth throttle on top of the application 24h rate limit.

    The 24h rate limit (cf. service) handles the legitimate use case. This
    throttle protects against a flood of 429s being used to enumerate user IDs
    if an attacker has stolen credentials but is already rate-limited.
    """

    scope = "gdpr_export_create"
    rate = "50/h"


class _GdprExportCursorPagination(CursorPagination):
    """Cursor pagination keyed on `requested_at` — the canonical timestamp for
    a GDPR export request (the global default `created` does not exist on the
    model).
    """

    ordering = "-requested_at"
    page_size = 50


class GdprExportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """REST surface for GDPR Article 20 exports (Story 1.11).

    - `POST /api/v1/me/gdpr-exports` — creates a pending export.
    - `GET  /api/v1/me/gdpr-exports` — paginated list of the caller's exports.
    - `GET  /api/v1/me/gdpr-exports/{id}` — single export status.
    - `GET  /api/v1/me/gdpr-exports/{id}/download` — 302 to a presigned S3 URL.

    All endpoints scope to `request.user.id`; cross-user IDs surface as 404
    (not 403) so we never leak the existence of someone else's export.
    """

    serializer_class = GdprExportRequestSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = _GdprExportCursorPagination
    lookup_field = "id"

    def get_throttles(self):
        if self.action == "create":
            return [_GdprExportCreateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return GdprExportRequest.objects.none()
        return GdprExportRequest.objects.filter(user_id=self.request.user.id)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        export = GdprExportService.request_export(user=request.user)
        serializer = self.get_serializer(export)
        return Response(serializer.data, status=drf_status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Request, id: str | None = None) -> Response:
        export = self.get_object()

        if export.status == GdprExportStatus.EXPIRED:
            raise GdprExportExpired()
        if export.status != GdprExportStatus.READY:
            raise GdprExportNotReady(
                detail=f"Cet export n'est pas encore prêt (statut : {export.status})."
            )
        # Lazy-expiry check (post-review patch): the nightly beat purges
        # expired rows at 04:00 UTC; between `expires_at` and the next beat
        # tick (up to ~24h), `status` is still READY though the row is logically
        # expired. Reject the download here to honour the 7-day contract.
        if export.expires_at and export.expires_at < timezone.now():
            raise GdprExportExpired()
        if not export.archive_s3_key:
            # Defensive: status=ready without an S3 key is an invariant violation.
            raise GdprExportNotReady(detail="Archive introuvable.")

        # Atomic cap enforcement (post-review patch — TOCTOU was bypassable by
        # concurrent requests both reading download_count < MAX before either
        # incremented). `.update(... = F(field) + 1)` with a guarded filter
        # returns the number of rows updated; if zero, another request already
        # hit the cap.
        updated = GdprExportRequest.objects.filter(
            pk=export.id,
            download_count__lt=settings.GDPR_EXPORT_MAX_DOWNLOADS,
        ).update(
            download_count=F("download_count") + 1,
            last_downloaded_at=timezone.now(),
        )
        if updated == 0:
            raise GdprExportDownloadCap()

        # Generate the presigned URL BEFORE writing the audit row, so a boto3
        # failure does not leave a phantom "downloaded" audit entry without an
        # actual redirect (post-review patch).
        try:
            s3 = gdpr_s3_client()
            presigned = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": settings.GDPR_EXPORTS_BUCKET,
                    "Key": export.archive_s3_key,
                },
                ExpiresIn=settings.GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS,
            )
        except Exception:
            # Roll back the counter we just claimed so the user can retry.
            GdprExportRequest.objects.filter(pk=export.id).update(
                download_count=F("download_count") - 1,
            )
            raise

        # Refetch the authoritative count post-update so the audit row reflects
        # actual ordering under concurrency (post-review patch — the previous
        # `new_count = stale + 1` produced duplicate values).
        export.refresh_from_db(fields=["download_count"])
        record_audit(
            action="gdpr.export_downloaded",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject_id=request.user.id,
            metadata={"export_id": export.id, "download_count": export.download_count},
        )

        return HttpResponseRedirect(presigned)


# --- Story 1.4 — Parental consent flow ----------------------------------------


def _ratelimit_key_by_consent_token(group, request) -> str:
    """Rate-limit `/decide/` per consent token.

    `key="post:token"` would only look at POST body fields; our token lives in the
    URL kwargs (`/parental-consent/<token>/decide/`). Returning empty string here
    would collapse every request into a single shared bucket — across users and
    tokens — which is what broke the test suite when running > 5 decide calls.

    Defensive: `request.resolver_match` is None in some middleware paths (tests
    using a bare RequestFactory, early-404 routes). Without this guard, the
    key callable raises `AttributeError` and django-ratelimit swallows the
    rate-limit entirely.
    """
    if request.resolver_match is None:
        return ""
    return request.resolver_match.kwargs.get("token", "")


def _age_today(birth_date: date | None) -> int | None:
    # Story 1.4 review §P24: return None (not 0) for a missing birth_date so the
    # parent landing page doesn't print "âge déclaré : 0 ans". The serializer
    # output stays an int-or-null; the frontend hides the line when null.
    if birth_date is None:
        return None
    return relativedelta(timezone.localdate(), birth_date).years


def _status_label(consent: ParentalConsent) -> str:
    """Map the (decision, expiry) tuple to the 4-state label the front consumes."""
    if consent.decision is not None:
        return consent.decision  # "granted" | "refused"
    if consent.is_expired:
        return "expired"
    return "pending"


@extend_schema(
    summary="Read a parental-consent token's state",
    description=(
        "Public endpoint used by the parent landing page. Returns the masked child "
        "email, the request timestamps, and the decision state. 404 if the token is "
        "unknown."
    ),
    responses={200: ParentalConsentStatusSerializer},
    auth=[],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def parental_consent_status(request: Request, token: str) -> Response:
    # The parent is authenticated by URL token, not by `request.user` — so RLS
    # sees an anonymous session and denies the SELECT on both `parental_consents`
    # and `users` (via select_related). Open the audited bypass for the duration
    # of this read-only lookup (Story 1.8 D3).
    with bypass_rls(
        reason="parental_consent.status_read",
        metadata={"token_prefix": token[:8] if token else ""},
    ):
        consent = ParentalConsent.objects.filter(token=token).select_related("student").first()
        if consent is None:
            raise ParentalConsentNotFound()
        payload = {
            "student_email_masked": mask_email(consent.student.email),
            "child_age": _age_today(consent.student.birth_date),
            "requested_at": consent.requested_at,
            "expires_at": consent.expires_at,
            "status": _status_label(consent),
        }
    return Response(ParentalConsentStatusSerializer(payload).data)


@extend_schema(
    summary="Record the parent's grant/refuse decision",
    description=(
        "Single-use semantics: once a decision is recorded, subsequent calls return "
        "409. The 60-day expiry also locks the token. Rate-limited 5/h/token."
    ),
    request=ParentalConsentDecisionSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "decision": {"type": "string", "enum": ["granted", "refused"]},
                "child_status": {"type": "string"},
            },
        }
    },
    auth=[],
)
@api_view(["POST"])
@permission_classes([AllowAny])
# Stacked rate-limit (Story 1.4 review §P2):
#   - 5/h per token: caps legitimate retry / double-click for a single decision.
#   - 60/h per IP: prevents an attacker from sweeping unknown tokens at high rate.
# django-ratelimit stacks both decorators; `request.limited` becomes True if either fires.
@ratelimit(key="ip", rate="60/h", block=False)
@ratelimit(key=_ratelimit_key_by_consent_token, rate="5/h", block=False)
def parental_consent_decide(request: Request, token: str) -> Response:
    if getattr(request, "limited", False):
        raise RateLimited(retry_after_seconds=3600)

    serializer = ParentalConsentDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # The parent is authenticated by URL token (Story 1.4 ADR-0003), not by
    # `request.user`. RLS sees an anonymous session and would deny every
    # SELECT/UPDATE on `parental_consents` + `users`. The audited bypass
    # opens for the duration of this endpoint (Story 1.8 D3).
    with bypass_rls(
        reason="parental_consent.decide",
        metadata={
            "token_prefix": token[:8] if token else "",
            "decision": serializer.validated_data["decision"],
        },
    ):
        consent = ParentalConsent.objects.filter(token=token).select_related("student").first()
        if consent is None:
            raise ParentalConsentNotFound()

        consent = record_decision(
            consent=consent,
            decision=serializer.validated_data["decision"],
            content_hash=serializer.validated_data["content_hash"],
            # Story 1.4 review §P26: pass client-supplied timestamp through so the
            # service can store it as `client_accepted_at` for forensic clock-drift
            # detection. `decided_at` stays server-authoritative.
            client_accepted_at=serializer.validated_data["accepted_at"],
            ip=_client_ip_from_request(request),
            user_agent=request.headers.get("user-agent"),
        )

        # Idempotent: only send the "granted" mail on the actual state change. If a
        # double-click squeezes past `select_for_update` (different worker / proc),
        # `record_decision` would raise AlreadyDecided and we'd never reach here.
        # Story 1.4 review §P14: stamp `notification_sent_at` only on success so the
        # reconciliation Celery task `notify_unconfirmed_granted_consents` retries
        # rows where SMTP failed at this point.
        if consent.decision == "granted" and send_granted_to_child(consent.student):
            consent.notification_sent_at = timezone.now()
            consent.save(update_fields=["notification_sent_at", "updated_at"])

        decision = consent.decision
        child_status = consent.student.status

    return Response({"decision": decision, "child_status": child_status})


@extend_schema(
    summary="Re-send the parental-consent email (child-initiated)",
    description=(
        "Authenticated endpoint — only the student themselves can resend their own "
        "consent email. Rate-limited 1/h/user."
    ),
    responses={
        200: {"type": "object", "properties": {"detail": {"type": "string"}}},
        404: None,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
# `user_or_ip` is the django-ratelimit built-in that resolves to `request.user.id` when
# authenticated and falls back to client IP otherwise — safe regardless of where the
# rate-limit decorator runs in the middleware chain (cf. Story 1.4 review §P10).
@ratelimit(key="user_or_ip", rate="1/h", block=False)
def parental_consent_resend(request: Request) -> Response:
    if getattr(request, "limited", False):
        raise RateLimited(retry_after_seconds=3600)

    # Story 1.4 review §P5: skip consents whose token has expired — sending a parent
    # link that immediately 409s on click is broken UX. The daily suspend job will
    # finalise the soft-suspend; until then the student can re-attempt signup.
    consent = (
        ParentalConsent.objects.filter(
            student=request.user,
            decision__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by("-requested_at")
        .first()
    )
    if consent is None:
        raise ParentalConsentNotFound()

    # §P16: use the reminder template (the "Vous n'avez pas encore répondu" copy) —
    # the child-initiated resend should not look like the initial request.
    # §P6: only flip reminder_sent_at on successful SMTP — otherwise the daily Celery
    # reminder job (which guards on `reminder_sent_at IS NULL`) would also skip the row.
    sent = send_reminder_to_parent(consent)
    if sent:
        consent.reminder_sent_at = timezone.now()
        consent.save(update_fields=["reminder_sent_at", "updated_at"])
        return Response({"detail": "Email parental renvoyé."})
    # SMTP failure surfaced as a generic 503-ish problem so the front can retry.
    raise RateLimited(retry_after_seconds=600)


def _client_ip_from_request(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# --- Story 1.12 — Account deletion (GDPR Article 17, right to erasure) --------


def _ratelimit_key_by_deletion_token(group, request) -> str:
    """Per-token rate-limit key for the public cancel endpoint.

    Same defensive shape as `_ratelimit_key_by_consent_token` — `resolver_match`
    can be None in some middleware paths (test RequestFactory, early 404).
    """
    if request.resolver_match is None:
        return ""
    return request.resolver_match.kwargs.get("token", "")


def _deletion_public_status_label(deletion: AccountDeletionRequest) -> str:
    """Map the (cancelled_at, hard_deleted_at, hard_delete_after) tuple to the
    4-state label the public landing consumes.
    """
    if deletion.hard_deleted_at is not None:
        return "hard_deleted"
    if deletion.cancelled_at is not None:
        return "cancelled"
    if deletion.is_past_grace_window:
        return "expired"
    return "pending_hard_delete"


@extend_schema(
    summary="Request account deletion (GDPR Article 17)",
    description=(
        "Soft-deletes the authenticated user, killing all their active sessions and "
        "scheduling a hard-delete cascade 30 days later. Returns 202 with the request "
        "metadata + cancel deadline. The cancel link is delivered via email only."
    ),
    request=AccountDeletionRequestPayloadSerializer,
    responses={202: AccountDeletionRequestSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
# Per-IP throttle: legitimate users may make 2-3 attempts (wrong password
# typos); above 3/24h is suspicious activity worth slowing down.
@ratelimit(key="ip", rate="3/24h", block=False)
def account_deletion_request(request: Request) -> Response:
    if getattr(request, "limited", False):
        raise RateLimited(retry_after_seconds=86400)

    payload = AccountDeletionRequestPayloadSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    deletion = account_deletion_service.request_deletion(
        user=request.user,
        password=payload.validated_data["password"],
        content_hash=payload.validated_data["content_hash"],
        accepted_at=payload.validated_data["accepted_at"],
        ip=_client_ip_from_request(request),
        user_agent=request.headers.get("user-agent"),
    )

    serialized = AccountDeletionRequestSerializer(deletion).data
    return Response(serialized, status=drf_status.HTTP_202_ACCEPTED)


@extend_schema(
    summary="Get my pending account-deletion request",
    description=(
        "Returns the authenticated user's in-flight account-deletion request (404 if "
        "none). The front uses this to disable the delete button + show the grace-"
        "window deadline when a request is already in flight."
    ),
    responses={200: AccountDeletionRequestSerializer, 404: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account_deletion_status_authenticated(request: Request) -> Response:
    deletion = account_deletion_service.lookup_active_request_for_user(request.user)
    if deletion is None:
        # Story 1.12 code review §P17: differentiate the "no in-flight request"
        # 404 from the public token endpoint's "unknown token" 404 by using a
        # dedicated Problem URI so the front can switch on `type`.
        raise AccountDeletionNoPending()
    return Response(AccountDeletionRequestSerializer(deletion).data)


@extend_schema(
    summary="Public lookup of an account-deletion request by token",
    description=(
        "Used by the public cancel landing page. Returns the masked email and the "
        "deadline so the user can recognise their account before re-authenticating."
    ),
    responses={200: AccountDeletionPublicStatusSerializer, 404: None},
    auth=[],
)
@api_view(["GET"])
@permission_classes([AllowAny])
# Per-IP rate-limit: someone enumerating tokens won't get far at this rate (256-bit
# entropy makes brute force impractical anyway), but we slow noise down in the logs.
@ratelimit(key="ip", rate="30/h", block=False)
def account_deletion_status_public(request: Request, token: str) -> Response:
    if getattr(request, "limited", False):
        raise RateLimited(retry_after_seconds=3600)

    deletion = account_deletion_service.lookup_request_by_token(token)
    # Story 1.12 code review §D3: anti-enumeration on terminal states. A
    # token whose row is cancelled / hard_deleted / past the grace window
    # leaks "yes Alice's account was deleted on date X" to anyone holding
    # the token (e.g. a leaked email forward). Return 404 instead of an
    # informative payload — the legitimate user opens an old cancel link and
    # sees the "lien invalide ou expiré" copy on the public landing, which
    # is the right UX for a window that's already closed.
    label = _deletion_public_status_label(deletion)
    if label in ("cancelled", "hard_deleted", "expired"):
        raise AccountDeletionNotFound()

    # Story 1.12 code review §P11: a row with `user=NULL` but no
    # `hard_deleted_at` is an invariant violation (cascade hasn't fired).
    # Refuse it instead of leaking a `***@***` placeholder to whoever held
    # the token.
    user_ref = deletion.user
    if user_ref is None:
        raise AccountDeletionNotFound()

    payload = {
        "user_email_masked": mask_email(user_ref.email),
        "requested_at": deletion.requested_at,
        "hard_delete_after": deletion.hard_delete_after,
        "status": label,
    }
    return Response(AccountDeletionPublicStatusSerializer(payload).data)


@extend_schema(
    summary="Cancel an account-deletion request (public, token-based)",
    description=(
        "Public endpoint used by the cancel-link landing. Re-authenticates the user "
        "against the CURRENT password hash and restores the account if the grace "
        "window has not expired. Single-use semantics — after the row is cancelled, "
        "subsequent calls return 409."
    ),
    request=AccountDeletionCancelPayloadSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {"detail": {"type": "string"}},
        }
    },
    auth=[],
)
@api_view(["POST"])
@permission_classes([AllowAny])
# Stacked rate-limit — Story 1.12 code review §P2 / AC5: 5/h per IP + 5/h per
# token. Tight enough to throttle a leaked-token replay attempt without
# locking out a legitimate user who typo'd their password twice. The 256-bit
# token entropy is the primary defence; these caps just slow log noise.
@ratelimit(key="ip", rate="5/h", block=False)
@ratelimit(key=_ratelimit_key_by_deletion_token, rate="5/h", block=False)
def account_deletion_cancel(request: Request, token: str) -> Response:
    if getattr(request, "limited", False):
        raise RateLimited(retry_after_seconds=3600)

    payload = AccountDeletionCancelPayloadSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    deletion = account_deletion_service.lookup_request_by_token(token)
    account_deletion_service.cancel_deletion(
        request=deletion,
        password=payload.validated_data["password"],
        cancel_reason="user_self_service",
    )

    return Response({"detail": "Ton compte est restauré. Tu peux te reconnecter."})


# --- Story 1.6 — MFA TOTP (6 endpoints) ----------------------------------------


class _MfaSessionPayload(serializers.Serializer):
    mfa_session = serializers.CharField(required=True, max_length=2048)


class _MfaEnrollConfirmPayload(_MfaSessionPayload):
    code = serializers.CharField(required=True, min_length=6, max_length=8)


class _MfaChallengePayload(_MfaSessionPayload):
    """Code-review P23 — accepts both 6-digit TOTP and `xxxx-xxxx-xxxx`
    recovery codes (14 chars). The `method` field is REQUIRED so a
    fat-fingered recovery code routed to TOTP verify doesn't burn a
    lockout slot.
    """

    code = serializers.CharField(required=True, min_length=6, max_length=20)
    method = serializers.ChoiceField(required=True, choices=["totp", "recovery"])


class _MfaReauthPayload(serializers.Serializer):
    """Payload for the authenticated MFA mutations (disable, regenerate).

    **TOTP-only step-up** (code-review D4) — recovery codes are NOT a valid
    second factor for self-service disable/regenerate. A user who has lost
    their authenticator must go through DPO reset, not destroy their MFA
    state with a single recovery code (which would let an attacker with one
    code drop MFA entirely).

    Requires the user's current password + a TOTP code as a "step-up" guard
    against session hijack: even if an attacker has the session cookie,
    they can't drop MFA or regenerate recovery codes without the password
    AND a fresh TOTP code.
    """

    password = serializers.CharField(required=True, max_length=200)
    code = serializers.CharField(required=True, min_length=6, max_length=8)


def _mfa_user_response(user) -> dict:
    """User envelope for MFA endpoints — same shape as login responses so the
    frontend's typed `User` model doesn't fork per endpoint.
    """
    from apps.accounts.serializers import UserDetailsSerializer

    return {"user": UserDetailsSerializer(user).data}


def _mfa_minimal_user(user) -> dict:
    """Scrubbed user envelope for the half-login response (before MFA confirm).

    Code-review D5 — the full `UserDetailsSerializer` leaks `email`,
    `mfa_recovery_codes_remaining`, etc. before the MFA challenge passes.
    The half-login response carries only what the frontend needs to route
    by role + render the right banner. Full profile comes after the
    challenge completes (`/auth/user/` round-trip OR the challenge
    endpoint's own response).
    """
    return {
        "id": user.id,
        "role": user.role,
        "status": user.status,
        "mfa_required_by_role": user.role in STAFF_ROLES_REQUIRING_MFA,
        "mfa_enrolled": user.has_mfa_enrolled,
    }


def _send_mfa_low_codes_email(request, user, remaining: int) -> None:
    """Best-effort low-codes warning, deduped per-user/day via cache.add lock
    (code-review P20 — concurrent recovery consumption would otherwise spam
    two emails).
    """
    from django.core.cache import cache

    dedup_key = f"mfa_low_email_sent:{user.id}"
    if not cache.add(dedup_key, "1", timeout=86400):
        # Already sent in the last 24h
        return
    try:
        from allauth.account.adapter import get_adapter

        get_adapter(request).send_mail(
            "account/email/mfa_recovery_low",
            user.email,
            {"user": user, "remaining": remaining},
        )
    except Exception:
        import structlog

        structlog.get_logger(__name__).warning(
            "auth.mfa_recovery_low.notify_failed", user_id=user.id, exc_info=True
        )


@extend_schema(
    summary="Start MFA enrollment — generate TOTP secret + QR code.",
    request=_MfaSessionPayload,
    responses={200: serializers.JSONField()},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def mfa_enroll_start_view(request: Request) -> Response:
    """Issue a new TOTP secret + QR code for the user identified by
    `mfa_session` (stage=`mfa_enrollment_pending`).

    No session cookie is required — the `mfa_session` token is the auth
    proof (it was issued at password-success by `ThrottledLoginView` OR
    by `mfa_enroll_start_from_session_view` for an authenticated B2C user
    opting into MFA — code-review D3).

    Code-review P1 — calls `record_use(token=...)` which blacklists the
    JTI after `MAX_USES_PER_TOKEN` (default 3) calls. The user may need to
    retry the QR-scan a couple of times, but a stolen token can't be
    replayed indefinitely within the 5-min TTL.

    Code-review P5 — refuses for an already-enrolled user (unless the
    DPO reset flag is set), preventing an attacker with a stale
    `mfa_enrollment_pending` token from creating a 2nd unconfirmed device.
    """
    from apps.accounts.gdpr_exceptions import MfaEnrollmentAlreadyComplete
    from apps.accounts.services import mfa as mfa_service
    from apps.accounts.services import mfa_session as mfa_session_service

    payload = _MfaSessionPayload(data=request.data)
    payload.is_valid(raise_exception=True)

    ip = _client_ip_from_request(request)
    token = payload.validated_data["mfa_session"]
    user = mfa_session_service.verify(
        token=token,
        request_ip=ip,
        expected_stage="mfa_enrollment_pending",
    )

    # Code-review P5 — refuse if already enrolled (unless DPO forced reset).
    try:
        profile = user.mfa_profile
        forced_re_enroll = profile.requires_enrollment_at_next_login
    except Exception:
        # No profile row yet → never enrolled, no force flag — allow start.
        forced_re_enroll = False
    if user.has_mfa_enrolled and not forced_re_enroll:
        raise MfaEnrollmentAlreadyComplete()

    # Code-review P1 — bump per-token use counter; the helper blacklists the
    # JTI after MAX_USES_PER_TOKEN calls.
    mfa_session_service.record_use(token=token)

    _device, otpauth_url, qr_svg = mfa_service.start_enrollment(
        user=user, ip_truncated=_truncate_ip_for_audit(ip)
    )
    return Response(
        {
            "otpauth_url": otpauth_url,
            "qr_svg": qr_svg,
            "issuer": "Path-Advisor",
            "account_label": user.email,
        }
    )


@extend_schema(
    summary=(
        "Mint an mfa_session for an authenticated B2C user opting into MFA "
        "(code-review D3 — replaces the prior logout-and-re-login flow)."
    ),
    request=None,
    responses={200: serializers.JSONField(), 403: serializers.JSONField()},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_enroll_start_from_session_view(request: Request) -> Response:
    """Issue an `mfa_session` token (stage=`mfa_enrollment_pending`) for the
    currently-authenticated user — used by the settings-page "Activer la MFA"
    CTA so the user does NOT have to log out and back in (code-review D3 +
    spec §AC2 in-place flow).

    Refuses if the user is already enrolled (idempotent — the settings page
    should never render the CTA in that state, but defend in depth).

    The minted token is bound to the user's IP at issue time. The user then
    POSTs it to `/mfa/enroll/start/` + `/mfa/enroll/confirm/` like a staff
    first-login flow. The current session cookie stays valid — the user is
    NOT logged out during enrollment.
    """
    from apps.accounts.gdpr_exceptions import MfaEnrollmentAlreadyComplete
    from apps.accounts.services import mfa_session as mfa_session_service

    user = request.user
    if user.has_mfa_enrolled:
        raise MfaEnrollmentAlreadyComplete()

    ip = _client_ip_from_request(request)
    token = mfa_session_service.issue(user=user, stage="mfa_enrollment_pending", ip=ip)
    return Response({"mfa_session": token, "mfa_enrollment_required": True})


@extend_schema(
    summary="Confirm MFA enrollment with the first TOTP code.",
    request=_MfaEnrollConfirmPayload,
    responses={200: serializers.JSONField(), 400: serializers.JSONField()},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def mfa_enroll_confirm_view(request: Request) -> Response:
    """Validate the first TOTP code, finalize enrollment, issue 8 recovery
    codes, and post the session cookie (full login completed).
    """
    from django.contrib.auth import login as django_login

    from apps.accounts.services import login_security
    from apps.accounts.services import mfa as mfa_service
    from apps.accounts.services import mfa_session as mfa_session_service

    payload = _MfaEnrollConfirmPayload(data=request.data)
    payload.is_valid(raise_exception=True)

    ip = _client_ip_from_request(request)
    ip_truncated = _truncate_ip_for_audit(ip)

    user = mfa_session_service.verify(
        token=payload.validated_data["mfa_session"],
        request_ip=ip,
        expected_stage="mfa_enrollment_pending",
    )

    plaintext_codes = mfa_service.confirm_enrollment(
        user=user,
        code=payload.validated_data["code"],
        ip_truncated=ip_truncated,
    )
    if not plaintext_codes:
        # Wrong code — write a failure audit row (the service skipped it
        # because the failure path needs the request context here).
        record_audit(
            action="auth.mfa_challenge_failed",
            result=AuditResult.FAILURE,
            actor=user,
            subject_id=user.id,
            metadata={
                "reason": "invalid_enrollment_code",
                "ip_truncated": ip_truncated,
            },
        )
        login_security.record_failed_attempt(user=user, ip_truncated=ip_truncated)
        from apps.accounts.gdpr_exceptions import MfaChallengeFailed

        raise MfaChallengeFailed()

    # Consume the mfa_session so it can't be reused
    mfa_session_service.consume(token=payload.validated_data["mfa_session"])

    # Clear lockout AFTER full login succeeded (cf. Story 1.5 code-review semantic
    # move — the password-only success no longer clears, only the MFA-full success).
    login_security.clear_failed_attempts(user=user, trigger="mfa_enrollment")

    # Post the session cookie via dj-rest-auth's login machinery
    # Multi-backend Django setup (allauth + ModelBackend) requires explicit
    # `backend=` since `login()` cannot disambiguate. ModelBackend is the right
    # choice because the user was just authenticated by dj-rest-auth's
    # serializer (which delegates to `authenticate()` → ModelBackend).
    django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return Response(
        {
            "recovery_codes": plaintext_codes,
            **_mfa_user_response(user),
        }
    )


@extend_schema(
    summary="Submit an MFA code (TOTP or recovery) to complete login.",
    request=_MfaChallengePayload,
    responses={200: serializers.JSONField(), 400: serializers.JSONField()},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def mfa_challenge_view(request: Request) -> Response:
    """Verify a TOTP / recovery code submitted with the `mfa_session` token
    issued at password-success. On success: post the session cookie + clear
    the lockout counter.

    **Code-review patches landed:**
    - P2: emit `auth.mfa_challenge_failed` with `reason="too_many_attempts"`
      when `record_failed_attempt` returns ≥ threshold.
    - P3: emit `auth.mfa_challenge_failed` with `reason="expired_session"`
      when the `mfa_session` JWT has expired (catch → audit → reraise).
    - P12: pre-check `user.is_locked` after JWT verify — a locked user can
      no longer consume `mfa_session` attempts.
    - P15: catch `MfaSessionConsumed` distinctly from `MfaSessionInvalid` so
      the frontend surfaces "already used, reconnect" copy.
    - P17/P27: wrap `verify_challenge` in try/except so a DB/audit failure
      still bumps the lockout counter (defense-in-depth).
    - P28: bump `record_failure(token=...)` on every failure — the JTI is
      blacklisted server-side after `MAX_FAILS_PER_TOKEN` (default 3) hits.
    """
    from django.contrib.auth import login as django_login

    from apps.accounts.gdpr_exceptions import (
        MfaChallengeFailed,
        MfaSessionConsumed,
        MfaSessionExpired,
        MfaSessionInvalid,
    )
    from apps.accounts.services import login_security
    from apps.accounts.services import mfa as mfa_service
    from apps.accounts.services import mfa_session as mfa_session_service

    payload = _MfaChallengePayload(data=request.data)
    payload.is_valid(raise_exception=True)

    ip = _client_ip_from_request(request)
    ip_truncated = _truncate_ip_for_audit(ip)
    token = payload.validated_data["mfa_session"]

    # P3: audit the expired-session case (DPO triage signal). The
    # MfaSessionExpired / MfaSessionConsumed surface up to the frontend as
    # distinct Problem Details types (P15).
    try:
        user = mfa_session_service.verify(token=token, request_ip=ip, expected_stage="mfa_pending")
    except MfaSessionExpired:
        record_audit(
            action="auth.mfa_challenge_failed",
            result=AuditResult.FAILURE,
            actor=None,
            subject_id=None,
            metadata={"reason": "expired_session", "ip_truncated": ip_truncated},
        )
        raise
    except (MfaSessionConsumed, MfaSessionInvalid):
        raise

    # P12 — pre-check lockout. The mfa_session JWT is valid but the user
    # is currently locked (password leg or prior MFA bursts). Refuse with
    # the same generic 400 the password lockout uses.
    if login_security.is_account_locked(user):
        raise AccountLocked()

    method = payload.validated_data["method"]

    # P27 — verify under try/except. A failure (DB outage, audit chain
    # error) must still bump the lockout counter so brute-force is throttled
    # even when the audit layer is degraded.
    ok = False
    try:
        ok = mfa_service.verify_challenge(
            user=user,
            code=payload.validated_data["code"],
            method=method,
            ip_truncated=ip_truncated,
        )
    except Exception:
        login_security.record_failed_attempt(user=user, ip_truncated=ip_truncated)
        mfa_session_service.record_failure(token=token)
        raise

    if not ok:
        # P28 — per-token failure counter (blacklists JTI on 3rd hit).
        mfa_session_service.record_failure(token=token)
        # Per-account lockout counter (Story 1.5 service — shared with the
        # password leg by design, see Story 1.6 §AC5).
        new_count = login_security.record_failed_attempt(user=user, ip_truncated=ip_truncated)
        # P2 — if the failure trip the lockout, emit a SECOND audit row
        # with `reason="too_many_attempts"` so DPO queries can spot the
        # threshold-trip distinctly from individual wrong-code attempts.
        threshold = getattr(settings, "LOGIN_FAIL_THRESHOLD", 5)
        if new_count >= threshold:
            record_audit(
                action="auth.mfa_challenge_failed",
                result=AuditResult.FAILURE,
                actor=user,
                subject_id=user.id,
                metadata={
                    "reason": "too_many_attempts",
                    "method": method,
                    "ip_truncated": ip_truncated,
                },
            )
        raise MfaChallengeFailed()

    # Single-use: blacklist the mfa_session JTI so it can NEVER be replayed.
    mfa_session_service.consume(token=token)

    # Clear lockout — full login succeeded.
    login_security.clear_failed_attempts(user=user, trigger="mfa_challenge")

    # P20 — low-codes warning email, deduped per-day via cache.add lock.
    if method == "recovery":
        threshold = getattr(settings, "MFA_RECOVERY_LOW_THRESHOLD", 2)
        remaining = mfa_service.remaining_recovery_codes(user)
        if remaining <= threshold:
            _send_mfa_low_codes_email(request, user, remaining)

    # Multi-backend Django setup (allauth + ModelBackend) requires explicit
    # `backend=` since `login()` cannot disambiguate. ModelBackend is the right
    # choice because the user was just authenticated by dj-rest-auth's
    # serializer (which delegates to `authenticate()` → ModelBackend).
    django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(_mfa_user_response(user))


@extend_schema(
    summary="Disable MFA (B2C only). Staff roles refused (NFR-S2).",
    request=_MfaReauthPayload,
    responses={200: serializers.JSONField(), 403: serializers.JSONField()},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_disable_view(request: Request) -> Response:
    """Self-service MFA disable for B2C. Re-auth required (password + TOTP).
    Refuses with 403 for staff roles.

    **Code-review patches landed:**
    - D4 — step-up is TOTP-only (`method="totp"` hard-coded; recovery codes
      are NOT a valid second factor for destructive MFA operations).
    - P6 — `disable()` runs BEFORE the email send. The previous order
      meant a `MfaDisableForbiddenForStaff` raised inside `disable()`
      would lie to staff users via an email saying their MFA was disabled.
    - P13 — `verify_challenge(emit_audit=False)` so the step-up code check
      does NOT pollute the login-flow audit log with `mfa_challenge_passed`
      rows. The `auth.mfa_disabled` row is the canonical event here.
    """
    from apps.accounts.gdpr_exceptions import MfaChallengeFailed
    from apps.accounts.services import mfa as mfa_service

    payload = _MfaReauthPayload(data=request.data)
    payload.is_valid(raise_exception=True)

    user = request.user
    ip = _client_ip_from_request(request)
    ip_truncated = _truncate_ip_for_audit(ip)

    if not user.check_password(payload.validated_data["password"]):
        raise MfaChallengeFailed()
    # D4 — TOTP only. The _MfaReauthPayload no longer carries `method`.
    if not mfa_service.verify_challenge(
        user=user,
        code=payload.validated_data["code"],
        method="totp",
        ip_truncated=ip_truncated,
        emit_audit=False,
    ):
        raise MfaChallengeFailed()

    # P6 — disable FIRST so a staff-role refusal doesn't email a lie.
    mfa_service.disable(user=user, trigger="user_self_service", ip_truncated=ip_truncated)

    # Best-effort confirmation email AFTER the disable commits.
    try:
        from allauth.account.adapter import get_adapter

        get_adapter(request).send_mail("account/email/mfa_disabled", user.email, {"user": user})
    except Exception:
        import structlog

        structlog.get_logger(__name__).warning(
            "auth.mfa_disabled.notify_failed", user_id=user.id, exc_info=True
        )

    return Response({"detail": "La MFA a été désactivée sur ton compte."})


@extend_schema(
    summary="Regenerate the 8 recovery codes (invalidates the prior set).",
    request=_MfaReauthPayload,
    responses={200: serializers.JSONField(), 400: serializers.JSONField()},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_regenerate_recovery_codes_view(request: Request) -> Response:
    """Issue a fresh batch of 8 recovery codes. Re-auth required.

    Returns the plaintext codes — the user MUST save them; the prior set is
    invalidated immediately.
    """
    from apps.accounts.gdpr_exceptions import MfaChallengeFailed
    from apps.accounts.services import mfa as mfa_service

    payload = _MfaReauthPayload(data=request.data)
    payload.is_valid(raise_exception=True)

    user = request.user
    ip = _client_ip_from_request(request)
    ip_truncated = _truncate_ip_for_audit(ip)

    if not user.check_password(payload.validated_data["password"]):
        raise MfaChallengeFailed()
    # D4 — TOTP only for step-up. P13 — don't pollute login-flow audit log.
    if not mfa_service.verify_challenge(
        user=user,
        code=payload.validated_data["code"],
        method="totp",
        ip_truncated=ip_truncated,
        emit_audit=False,
    ):
        raise MfaChallengeFailed()

    codes = mfa_service.regenerate_recovery_codes(user=user, ip_truncated=ip_truncated)
    return Response({"recovery_codes": codes})


# Rate-limit decorators applied via wrappers — see urls.py (we use api_view
# above so the existing `@ratelimit` chain works at URL-wire time).
