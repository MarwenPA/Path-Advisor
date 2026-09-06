"""Establishments app serializers — Story 6.5."""

from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.establishments.models import (
    CohortImportJob,
    CounselorConsent,
    CounselorInvitation,
    Establishment,
    EstablishmentType,
    LicenseType,
    StudentImportInvitationStatus,
)


class EstablishmentCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(choices=EstablishmentType.choices)
    city = serializers.CharField(max_length=120)
    uai = serializers.CharField(max_length=20)
    contact_name = serializers.CharField(max_length=200)
    contact_email = serializers.EmailField()
    license_start = serializers.DateField()
    license_end = serializers.DateField()
    license_type = serializers.ChoiceField(choices=LicenseType.choices)


class EstablishmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Establishment
        fields = [
            "id",
            "name",
            "type",
            "city",
            "uai",
            "contact_name",
            "contact_email",
            "license_start",
            "license_end",
            "license_type",
            "is_active",
            "created_at",
        ]


class CohortCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    school_year = serializers.CharField(max_length=20)


class CohortSerializer(serializers.Serializer):
    id = serializers.CharField()
    establishment_id = serializers.UUIDField()
    name = serializers.CharField()
    school_year = serializers.CharField()
    tenant_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()


class CohortImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortImportJob
        fields = [
            "id",
            "status",
            "total_rows",
            "imported_count",
            "skipped_count",
            "errors",
            "created_at",
            "completed_at",
        ]


class CounselorInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()


class CounselorInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounselorInvitation
        fields = ["id", "email", "status", "created_at", "expires_at", "accepted_at"]


class CounselorInvitationAcceptSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


class StudentInvitationPublicSerializer(serializers.Serializer):
    establishment_name = serializers.CharField()
    status = serializers.ChoiceField(choices=StudentImportInvitationStatus.choices)


class StudentInvitationAcceptSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


# --- Story 6.7 — counselor consent -------------------------------------------


class CounselorConsentSerializer(serializers.ModelSerializer):
    """A pending/decided consent request, as seen by the student."""

    counselor_email = serializers.EmailField(source="counselor.email", read_only=True)

    class Meta:
        model = CounselorConsent
        fields = [
            "id",
            "counselor_email",
            "status",
            "requested_at",
            "decided_at",
        ]
        read_only_fields = fields


class ConsentDecisionSerializer(serializers.Serializer):
    granted = serializers.BooleanField()
