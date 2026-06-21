"""Serializers for the Schools & Formations referential — Story 4.1 / 4.2 / 4.3 / 4.6 / 4.7."""

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
    """Serializer for Parcours — Story 4.3 graphe + Story 4.6 filter metadata + Story 4.7 dates.

    Story 4.3: base fields (profession, target_school, nodes, edges, niveau_scolaire, is_default).
    Story 4.6: denormalized filter metadata (tuition_max, selectivity, apprenticeship, internship)
    so the front-end can apply client-side filtering without extra round-trips.
    Story 4.7: label field, target_school_affelnet_dates, target_school_parcoursup_dates for
    admission date display per niveau scolaire.
    """

    target_school_name = serializers.SerializerMethodField()
    target_school_slug = serializers.SerializerMethodField()
    target_school_city = serializers.SerializerMethodField()
    # Story 4.7 — admission date fields
    target_school_affelnet_dates = serializers.SerializerMethodField()
    target_school_parcoursup_dates = serializers.SerializerMethodField()
    # Story 4.6 filter fields
    target_school_tuition_max = serializers.SerializerMethodField()
    target_school_selectivity = serializers.SerializerMethodField()
    target_school_apprenticeship = serializers.SerializerMethodField()
    target_school_internship = serializers.SerializerMethodField()

    class Meta:
        model = Parcours
        fields = [
            "id",
            "profession",
            "target_school",
            "target_school_name",
            "target_school_slug",
            "target_school_city",
            "nodes",
            "edges",
            "niveau_scolaire",
            "is_default",
            "label",
            "created_at",
            "updated_at",
            # Story 4.7 admission dates
            "target_school_affelnet_dates",
            "target_school_parcoursup_dates",
            # Story 4.6 filter fields
            "target_school_tuition_max",
            "target_school_selectivity",
            "target_school_apprenticeship",
            "target_school_internship",
        ]

    def get_target_school_name(self, obj: Parcours) -> str | None:
        return obj.target_school.name if obj.target_school else None

    def get_target_school_slug(self, obj: Parcours) -> str | None:
        return obj.target_school.slug if obj.target_school else None

    def get_target_school_city(self, obj: Parcours) -> str | None:
        return obj.target_school.city if obj.target_school else None

    def get_target_school_affelnet_dates(self, obj: Parcours) -> dict | None:
        return obj.target_school.affelnet_dates if obj.target_school else None

    def get_target_school_parcoursup_dates(self, obj: Parcours) -> dict | None:
        return obj.target_school.parcoursup_dates if obj.target_school else None

    def get_target_school_tuition_max(self, obj: Parcours) -> int | None:
        return obj.target_school.tuition_max_eur if obj.target_school else None

    def get_target_school_selectivity(self, obj: Parcours) -> int | None:
        return obj.target_school.selectivity_index if obj.target_school else None

    def get_target_school_apprenticeship(self, obj: Parcours) -> bool | None:
        return obj.target_school.apprenticeship if obj.target_school else None

    def get_target_school_internship(self, obj: Parcours) -> bool | None:
        return obj.target_school.internship if obj.target_school else None
