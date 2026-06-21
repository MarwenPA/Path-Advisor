"""Serializers for the Schools & Formations referential — Story 4.1 / 4.2 / 4.6."""

from __future__ import annotations

from rest_framework import serializers

from apps.schools.models import AdmissionStat, Formation, Parcours, School


class FormationInlineSerializer(serializers.ModelSerializer):
    """Compact formation representation nested inside SchoolDetailSerializer."""

    class Meta:
        model = Formation
        fields = ("id", "name", "duration_years", "parcoursup_open", "affelnet_open")
        read_only_fields = fields


class SchoolNestedSerializer(serializers.ModelSerializer):
    """Minimal school reference nested inside FormationAdminSerializer."""

    class Meta:
        model = School
        fields = ("id", "slug", "name")
        read_only_fields = fields


class SchoolAdminSerializer(serializers.ModelSerializer):
    """Full school representation for admin users — includes all fields + inline formations."""

    formations = FormationInlineSerializer(many=True, read_only=True)

    class Meta:
        model = School
        fields = (
            "id",
            "slug",
            "name",
            "type",
            "city",
            "region",
            "postal_code",
            "lat",
            "lon",
            "tuition_min_eur",
            "tuition_max_eur",
            "apprenticeship",
            "internship",
            "selectivity_index",
            "public_private",
            "description",
            "top_debouches",
            "parcoursup_dates",
            "affelnet_dates",
            "official_url",
            "formations",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class FormationAdminSerializer(serializers.ModelSerializer):
    """Full formation representation for admin users — includes nested school."""

    school = SchoolNestedSerializer(read_only=True)

    class Meta:
        model = Formation
        fields = (
            "id",
            "name",
            "school",
            "duration_years",
            "parcoursup_open",
            "affelnet_open",
            "created_at",
        )
        read_only_fields = fields


class SchoolDetailSerializer(serializers.ModelSerializer):
    """Full school representation for authenticated users — includes formations list."""

    formations = FormationInlineSerializer(many=True, read_only=True)

    class Meta:
        model = School
        fields = (
            "id",
            "slug",
            "name",
            "type",
            "city",
            "region",
            "postal_code",
            "lat",
            "lon",
            "tuition_min_eur",
            "tuition_max_eur",
            "apprenticeship",
            "internship",
            "selectivity_index",
            "public_private",
            "description",
            "top_debouches",
            "parcoursup_dates",
            "affelnet_dates",
            "official_url",
            "formations",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AdmissionStatSerializer(serializers.ModelSerializer):
    """Serializer for AdmissionStat — Story 4.2 prediction output."""

    class Meta:
        model = AdmissionStat
        fields = (
            "id",
            "school",
            "user",
            "min_proba",
            "expected_proba",
            "max_proba",
            "label",
            "context_line",
            "action_lever",
            "previous_proba",
            "updated_at",
            "created_at",
        )
        read_only_fields = fields


class ParcoursSerializer(serializers.ModelSerializer):
    """Serializer for Parcours — Story 4.6 filter support.

    Exposes denormalized target_school metadata so the front-end can apply
    client-side filtering (cost, selectivity, mode) without extra round-trips.
    """

    target_school_name = serializers.CharField(source="target_school.name", read_only=True)
    target_school_tuition_max = serializers.IntegerField(
        source="target_school.tuition_max_eur", read_only=True, allow_null=True
    )
    target_school_selectivity = serializers.IntegerField(
        source="target_school.selectivity_index", read_only=True
    )
    target_school_apprenticeship = serializers.BooleanField(
        source="target_school.apprenticeship", read_only=True
    )
    target_school_internship = serializers.BooleanField(
        source="target_school.internship", read_only=True
    )

    class Meta:
        model = Parcours
        fields = (
            "id",
            "nodes",
            "edges",
            "target_school_name",
            "target_school_tuition_max",
            "target_school_selectivity",
            "target_school_apprenticeship",
            "target_school_internship",
        )
        read_only_fields = fields
