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

from apps.accounts.models import GdprExportRequest
from apps.core.exceptions import AgeUnder15, ConsentRgpdRequired, EmailAlreadyRegistered


class SignupSerializer(RegisterSerializer):
    """Student signup serializer (Story 1.3 — ≥ 15 ans flow)."""

    username = None  # email-only authentication; drop allauth's optional username.
    birth_date = serializers.DateField(required=True)
    consent_rgpd_accepted = serializers.BooleanField(required=True)
    consent_cgu_version = serializers.CharField(required=True, max_length=20)

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
        age = relativedelta(today, value).years
        if age < 15:
            raise AgeUnder15()
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Object-level duplicate check that does NOT surface as field-level errors.

        dj-rest-auth's default `validate_email` only blocks already-verified duplicates
        so users can re-signup if they never confirmed; we want to block ANY duplicate
        (verified or not). Doing the check here ensures the resulting `DomainError`
        propagates as a generic Problem (no `errors.email`), preventing user enumeration.
        """
        attrs = super().validate(attrs)
        email = attrs.get("email")
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
