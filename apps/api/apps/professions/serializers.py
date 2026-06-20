"""Serializers for the Profession referential — Story 3.2 T1/T3, Story 3.8."""

from __future__ import annotations

from rest_framework import serializers

from apps.professions.models import Profession, ProfessionReport


class ProfessionPublicSerializer(serializers.ModelSerializer):
    """Fields exposed to authenticated students (no internal traceability data)."""

    class Meta:
        model = Profession
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "daily_routine",
            "requirements_json",
            "prospects_text",
            "median_salary_eur",
            "salary_range_json",
            "signals_json",
            "level_compatibility",
            "sector",
            "is_active",
        ]
        read_only_fields = fields


class ProfessionReportCreateSerializer(serializers.ModelSerializer):
    """Validates the student report payload — Story 3.8 AC4."""

    error_type = serializers.ChoiceField(choices=ProfessionReport.ErrorType.choices)
    comment = serializers.CharField(
        max_length=500, required=False, allow_null=True, allow_blank=True
    )
    location = serializers.CharField(
        max_length=300, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = ProfessionReport
        fields = ["error_type", "location", "comment"]


class ProfessionReportResponseSerializer(serializers.ModelSerializer):
    """Response shape for 201 Created — { id, status }."""

    class Meta:
        model = ProfessionReport
        fields = ["id", "status"]
        read_only_fields = fields


class ProfessionReportAdminSerializer(serializers.ModelSerializer):
    """Full representation for admin list — Story 3.8 AC6."""

    profession_slug = serializers.CharField(source="profession.slug", read_only=True)
    reporter_id = serializers.CharField(source="reporter.id", read_only=True, allow_null=True)

    class Meta:
        model = ProfessionReport
        fields = [
            "id",
            "profession_slug",
            "reporter_id",
            "error_type",
            "location",
            "comment",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class ProfessionAdminSerializer(serializers.ModelSerializer):
    """Full representation for admin users (includes sources, rome_code, audit fields)."""

    class Meta:
        model = Profession
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "daily_routine",
            "requirements_json",
            "prospects_text",
            "median_salary_eur",
            "salary_range_json",
            "signals_json",
            "level_compatibility",
            "sector",
            "rome_code",
            "sources_json",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
