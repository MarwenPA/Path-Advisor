"""Signup payload — extends dj-rest-auth's RegisterSerializer with Path-Advisor fields.

The `email`, `password1`, `password2` fields come from the parent. We add:
- `birth_date` — required; validated to enforce age ≥ 15 (Story 1.3 §AC2).
- `consent_rgpd_accepted` — required; must be `True`.
- `consent_cgu_version` — required; recorded so we can re-prompt users when CGU change.

Duplicate-email handling is intentionally performed at the **object** validation level
(`validate()`), not the field level (`validate_email`). Field-level validators surface
their errors under `errors.email` in the Problem JSON, which trivially leaks the existence
of an account (CWE-203). Raising a `DomainError` from `validate()` propagates as a plain
Problem with a generic `detail`, leaving no field-level breadcrumb.

Note: per dj-rest-auth convention `password1`/`password2` are accepted on the wire.
The front-end form is encouraged to expose them as a single password field +
client-side confirm, mapping to both keys at submit time.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from dateutil.relativedelta import relativedelta
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import AccountDeletionRequest, GdprExportRequest
from apps.core.exceptions import (
    ConsentRgpdRequired,
    EmailAlreadyRegistered,
    ParentEmailNotApplicable,
    ParentEmailRequired,
    ParentEmailSameAsStudent,
)


class SignupSerializer(RegisterSerializer):
    """Student signup serializer (Story 1.3 ≥ 15 + Story 1.4 < 15 parental branch)."""

    username = None  # email-only authentication; drop allauth's optional username.
    birth_date = serializers.DateField(required=True)
    consent_rgpd_accepted = serializers.BooleanField(required=True)
    consent_cgu_version = serializers.CharField(required=True, max_length=20)
    # Optional; mandatory iff age < 15 (enforced in `validate()` once both fields are known).
    parent_email = serializers.EmailField(required=False, allow_blank=False)

    def validate_consent_rgpd_accepted(self, value: bool) -> bool:
        if not value:
            raise ConsentRgpdRequired()
        return value

    def validate_birth_date(self, value: date) -> date:
        today = timezone.localdate()
        # Future birth-dates would produce a negative `relativedelta.years` and slip
        # past the < 15 check; reject them explicitly first.
        if value > today:
            raise serializers.ValidationError("Date de naissance invalide.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Object-level validation: branch on `(age, parent_email)` and check duplicates.

        Cross-field rules live here so that the (age, parent_email) decision matrix can
        see both fields together — field-level validators run independently and can't
        coordinate. Duplicate-email check also stays here so the resulting `DomainError`
        propagates as a generic Problem (no `errors.email`), preventing CWE-203 enumeration.
        """
        attrs = super().validate(attrs)

        birth_date = attrs.get("birth_date")
        parent_email = attrs.get("parent_email") or None
        email = attrs.get("email")

        # Age branching — only computed if birth_date passed field-level validation.
        if birth_date is not None:
            today = timezone.localdate()
            age = relativedelta(today, birth_date).years
            is_minor = age < 15
            if is_minor and not parent_email:
                raise ParentEmailRequired()
            if not is_minor and parent_email:
                raise ParentEmailNotApplicable()

        if email and parent_email and parent_email.lower() == email.lower():
            raise ParentEmailSameAsStudent()

        if email and get_user_model().objects.filter(email__iexact=email).exists():
            raise EmailAlreadyRegistered()

        return attrs

    def get_cleaned_data(self) -> dict[str, Any]:
        # Use `.get()` everywhere — if a field-level validator skipped a key, we
        # surface a single 400 from the missing-field branch rather than a 500.
        cleaned = super().get_cleaned_data()
        cleaned.update(
            {
                "birth_date": self.validated_data.get("birth_date"),
                "consent_rgpd_accepted": self.validated_data.get("consent_rgpd_accepted"),
                "consent_cgu_version": self.validated_data.get("consent_cgu_version"),
                "parent_email": self.validated_data.get("parent_email"),
            }
        )
        return cleaned


class GdprExportRequestSerializer(serializers.ModelSerializer):
    """Read-only serializer for GdprExportRequest (Story 1.11).

    Every field is read-only — the only mutation a client can do is POST to
    create a new request; status, S3 keys, and download counts all flow from
    the server.
    """

    class Meta:
        model = GdprExportRequest
        fields = (
            "id",
            "status",
            "requested_at",
            "ready_at",
            "expires_at",
            "download_count",
            "error_code",
            "error_message",
        )
        read_only_fields = fields


class UserDetailsSerializer(serializers.Serializer):
    """Read shape for the authenticated user (Story 1.4 — exposes `is_fully_active`).

    Replaces dj-rest-auth's default `UserDetailsSerializer` so the front can gate the
    "limited mode" banner on a single derived flag rather than reconstructing the rule
    `email_verified_at is not None AND status == "active"` client-side.

    Story 1.4 review §P17: this is **read-only by design**. dj-rest-auth's default
    serializer accepts PUT/PATCH on `/api/v1/auth/user/` to update profile fields,
    but we have no such fields on the custom User model yet. Without the explicit
    `update()` raise below, PATCH would return 200 with the request data echoed
    back and no DB write — a silent regression. Self-service profile editing
    will ship in a dedicated story (Epic 2 onboarding or 1.12 account deletion).
    """

    id = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_fully_active = serializers.BooleanField(read_only=True)

    # Story 1.6 — MFA state for the frontend dashboard banner / settings page.
    # `mfa_required_by_role` is the NFR-S2 forced-MFA flag (staff roles); the
    # frontend uses it to render the "MFA obligatoire pour ton rôle" banner
    # for staff who haven't yet enrolled. `mfa_enrolled` is the actual state.
    # `mfa_recovery_codes_remaining` drives the low-codes warning on the
    # settings page. NEVER includes the codes themselves — only a count.
    mfa_required_by_role = serializers.SerializerMethodField()
    mfa_enrolled = serializers.SerializerMethodField()
    mfa_recovery_codes_remaining = serializers.SerializerMethodField()

    def get_mfa_required_by_role(self, obj) -> bool:
        from apps.accounts.models import STAFF_ROLES_REQUIRING_MFA

        return obj.role in STAFF_ROLES_REQUIRING_MFA

    def get_mfa_enrolled(self, obj) -> bool:
        return obj.has_mfa_enrolled

    def get_mfa_recovery_codes_remaining(self, obj) -> int:
        from apps.accounts.services import mfa as _mfa

        return _mfa.remaining_recovery_codes(obj)

    def update(self, instance: object, validated_data: dict) -> object:
        from apps.core.exceptions import InsufficientPermissions

        raise InsufficientPermissions(
            detail="L'édition du profil via /api/v1/auth/user/ n'est pas disponible. Utilisez l'endpoint dédié quand il sera livré."
        )


class ParentalConsentStatusSerializer(serializers.Serializer):
    """Public read-shape returned by `GET /api/v1/auth/parental-consent/{token}/`.

    Carries the masked child email so the parent can recognise their child by
    context without the API revealing the full address (Story 1.4 §AC4).
    """

    student_email_masked = serializers.CharField()
    # Story 1.4 review §P24: null when the underlying user has no `birth_date`.
    child_age = serializers.IntegerField(allow_null=True)
    requested_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=["pending", "granted", "refused", "expired"])


class AccountDeletionRequestPayloadSerializer(serializers.Serializer):
    """Body of `POST /api/v1/auth/me/account-deletion/`.

    The password is the user's CURRENT password — re-asked for sensitive
    operation re-authentication (Story 1.12 §AC1, NIST 800-63B SP). Never
    persisted in cleartext; the service hashes it via `make_password()` into
    `password_hash_at_request` for forensic continuity.

    Story 1.12 §D2 follow-up: `content_hash` (SHA-256 hex from the ConsentDialog,
    Story 1.14 §AC5) + `accepted_at` (ISO 8601 from the client clock) prove
    what copy the user saw at decision time. Stored in the audit metadata
    alongside the deletion request — FR12 immutability evidence.
    """

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        min_length=1,
        max_length=128,
        trim_whitespace=False,
    )
    content_hash = serializers.RegexField(
        regex=r"^[0-9a-f]{64}$",
        required=True,
        help_text="Lowercase SHA-256 hex from the ConsentDialog payload.",
    )
    accepted_at = serializers.DateTimeField(required=True)


class AccountDeletionCancelPayloadSerializer(serializers.Serializer):
    """Body of `POST /api/v1/auth/account-deletion/<token>/cancel/`.

    Same password contract as the request payload — checked against the user's
    CURRENT hash (not `password_hash_at_request`), so a user who rotated the
    password via support during the grace window can still cancel (Story 1.12
    §4.5 #4).
    """

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        min_length=1,
        max_length=128,
        trim_whitespace=False,
    )


class AccountDeletionRequestSerializer(serializers.ModelSerializer):
    """Authenticated read-shape — used by `POST` 202 response + `GET /me/account-deletion/`.

    Carries the deadline so the front can render the grace-window countdown.
    Excludes the cancel_token and password hashes — those NEVER cross an API
    surface (cancel link goes via email; the hash is forensics-only).

    Story 1.12 code review §P18 / AC1 example response shape: also exposes a
    derived `status` label (the same 4-state machine the public endpoint uses)
    and a static `detail` string that the front can show without computing
    state itself.
    """

    status = serializers.SerializerMethodField()
    detail = serializers.SerializerMethodField()

    class Meta:
        model = AccountDeletionRequest
        fields = (
            "id",
            "status",
            "requested_at",
            "hard_delete_after",
            "cancelled_at",
            "hard_deleted_at",
            "detail",
        )
        read_only_fields = fields

    def get_status(self, obj: AccountDeletionRequest) -> str:
        if obj.hard_deleted_at:
            return "hard_deleted"
        if obj.cancelled_at:
            return "cancelled"
        if obj.is_past_grace_window:
            return "expired"
        return "pending_hard_delete"

    def get_detail(self, obj: AccountDeletionRequest) -> str:
        state = self.get_status(obj)
        if state == "pending_hard_delete":
            return (
                "Ton compte est désactivé. Tu as 30 jours pour annuler via "
                "le lien envoyé par email avant suppression définitive."
            )
        if state == "cancelled":
            return "Ta demande de suppression a été annulée."
        if state == "hard_deleted":
            return "Ton compte et tes données ont été supprimés définitivement."
        return "Le délai de 30 jours pour annuler est dépassé."


class AccountDeletionPublicStatusSerializer(serializers.Serializer):
    """Public read-shape returned by `GET /api/v1/auth/account-deletion/<token>/`.

    Carries the masked email so the user can recognise the account from the
    cancel-landing page without the endpoint leaking the full address (matches
    the parental-consent public-status pattern from Story 1.4).
    """

    user_email_masked = serializers.CharField()
    requested_at = serializers.DateTimeField()
    hard_delete_after = serializers.DateTimeField()
    status = serializers.ChoiceField(
        choices=["pending_hard_delete", "cancelled", "hard_deleted", "expired"]
    )


class ParentalConsentDecisionSerializer(serializers.Serializer):
    """Body of `POST /api/v1/auth/parental-consent/{token}/decide/`.

    `content_hash` is the 8-field SHA-256 from the ConsentDialog (Story 1.14); it is
    stored on the consent row as the immutability proof of what the parent saw.
    """

    decision = serializers.ChoiceField(choices=["granted", "refused"])
    content_hash = serializers.RegexField(
        regex=r"^[0-9a-f]{64}$",
        required=True,
        help_text="Lowercase SHA-256 hex from the ConsentDialog payload.",
    )
    accepted_at = serializers.DateTimeField(required=True)


# ---------------------------------------------------------------------------
# Story 1.5 — Password reset
# ---------------------------------------------------------------------------


class PathAdvisorPasswordResetSerializer:
    """Overrides dj-rest-auth's `PasswordResetSerializer.get_email_options()` to
    inject a Next.js-aware `url_generator` callable (Story 1.5 §AC5).

    `AllAuthPasswordResetForm.save()` accepts a `url_generator(request, user,
    token) -> str` kwarg via the options dict. We delegate to the existing
    `PathAdvisorAccountAdapter.get_password_reset_url` so URL building stays
    in one place (mirrors the verify-email URL helper from Story 1.3).

    Implemented as a delayed import / lazy class to avoid the dj-rest-auth
    AppRegistryNotReady issue at module load — defined inline at module
    bottom so Django app loading completes before the subclass is built.
    """

    def __new__(cls, *args, **kwargs):
        # Lazy-build the real subclass on first call to avoid the
        # `from dj_rest_auth.serializers import PasswordResetSerializer`
        # triggering `django.contrib.auth.models` import before Django apps
        # are ready (only matters at module-load time on cold starts).
        #
        # Double-checked locking — under cold-start contention two workers
        # would otherwise race the build; the loser-thread's `_Real` would
        # be a different class object, breaking `isinstance` checks elsewhere
        # (code-review P6 — Story 1.5 review 2026-05-27).
        global _RealPathAdvisorPasswordResetSerializer
        if _RealPathAdvisorPasswordResetSerializer is None:
            with _RealPasswordResetSerializerLock:
                if _RealPathAdvisorPasswordResetSerializer is None:
                    _RealPathAdvisorPasswordResetSerializer = _build_password_reset_serializer()
        return _RealPathAdvisorPasswordResetSerializer(*args, **kwargs)


import threading as _threading  # noqa: E402

_RealPasswordResetSerializerLock = _threading.Lock()
_RealPathAdvisorPasswordResetSerializer = None


def _build_password_reset_serializer():
    from allauth.account.utils import user_pk_to_url_str
    from dj_rest_auth.serializers import PasswordResetSerializer

    class _Real(PasswordResetSerializer):
        def get_email_options(self):
            # `AllAuthPasswordResetForm.save()` reads `url_generator` from
            # kwargs and calls it as `url_generator(request, user, token)`.
            # We rebuild the same URL the front-end serves at
            # `/auth/reset-password/<uid>/<token>` so the email link lands on
            # the SPA form instead of allauth's default Django page.
            from allauth.account.adapter import get_adapter

            def url_generator(request, user, token):
                return get_adapter(request).get_password_reset_url(
                    request,
                    uid=user_pk_to_url_str(user),
                    token=token,
                )

            return {"url_generator": url_generator}

    return _Real
