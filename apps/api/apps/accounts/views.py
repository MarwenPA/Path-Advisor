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
from django.db import IntegrityError
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import ParentalConsent
from apps.accounts.serializers import (
    ParentalConsentDecisionSerializer,
    ParentalConsentStatusSerializer,
)
from apps.accounts.services.parental_consent import record_decision
from apps.accounts.services.parental_consent_email import (
    send_granted_to_child,
    send_reminder_to_parent,
)
from apps.core.exceptions import (
    EmailAlreadyRegistered,
    ParentalConsentAlreadyDecided,
    ParentalConsentNotFound,
    RateLimited,
)
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

    consent = ParentalConsent.objects.filter(token=token).select_related("student").first()
    if consent is None:
        raise ParentalConsentNotFound()

    try:
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
    except ParentalConsentAlreadyDecided:
        # Already-decided or expired — surface the standard 409 Problem Details.
        raise

    # Idempotent: only send the "granted" mail on the actual state change. If a
    # double-click squeezes past `select_for_update` (different worker / proc),
    # `record_decision` would raise AlreadyDecided and we'd never reach here.
    # Story 1.4 review §P14: stamp `notification_sent_at` only on success so the
    # reconciliation Celery task `notify_unconfirmed_granted_consents` retries
    # rows where SMTP failed at this point.
    if consent.decision == "granted" and send_granted_to_child(consent.student):
        consent.notification_sent_at = timezone.now()
        consent.save(update_fields=["notification_sent_at", "updated_at"])

    return Response(
        {
            "decision": consent.decision,
            "child_status": consent.student.status,
        }
    )


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
