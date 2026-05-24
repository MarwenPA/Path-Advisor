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
