"""Serializers for the Schools & Formations referential — Story 4.1 / 4.2 / 4.3 / 4.6."""

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
    """Serializer for Parcours — Story 4.3 graphe parcours + Story 4.6 filter metadata.

    Story 4.3: base fields (profession, target_school, nodes, edges, niveau_scolaire, is_default).
    Story 4.6: denormalized filter metadata (tuition_max, selectivity, apprenticeship, internship)
    so the front-end can apply client-side filtering without extra round-trips.
    """

    target_school_name = serializers.SerializerMethodField()
    target_school_slug = serializers.SerializerMethodField()
    target_school_city = serializers.SerializerMethodField()
    # Story 4.6 filter fields
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
            "created_at",
            # Story 4.6 filter fields
            "target_school_tuition_max",
            "target_school_selectivity",
            "target_school_apprenticeship",
            "target_school_internship",
        ]

    def get_target_school_name(self, obj: Parcours) -> str:
        return obj.target_school.name

    def get_target_school_slug(self, obj: Parcours) -> str:
        return obj.target_school.slug

    def get_target_school_city(self, obj: Parcours) -> str:
        return obj.target_school.city
