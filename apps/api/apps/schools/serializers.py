"""Serializers for the Schools & Formations referential — Story 4.1 / 4.2 / 4.3 / 4.5."""

from __future__ import annotations

import logging

from django.utils import timezone
from rest_framework import serializers

from apps.schools.models import AdmissionStat, Formation, Parcours, School

logger = logging.getLogger(__name__)


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


class AdmissionStatSerializer(serializers.ModelSerializer):
    """Serializer for AdmissionStat — Story 4.2 prediction output."""

    updated_recently = serializers.SerializerMethodField()

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
            "updated_recently",
        )
        read_only_fields = fields

    def get_updated_recently(self, stat: AdmissionStat) -> bool:
        """True if the stat was updated within the last 24 hours (AC4 badge)."""
        return (timezone.now() - stat.updated_at).total_seconds() < 86400


class SchoolDetailSerializer(serializers.ModelSerializer):
    """Full school representation for authenticated users — includes formations list.

    Story 4.5: adds admission_stat SerializerMethodField that resolves the user-specific
    or baseline AdmissionStat row for this school (AC1, AC5).
    """

    formations = FormationInlineSerializer(many=True, read_only=True)
    admission_stat = serializers.SerializerMethodField()

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
            "admission_stat",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_admission_stat(self, school: School) -> dict | None:
        """Return personalised or baseline AdmissionStat for this school.

        Priority:
          1. Row matching the authenticated user (personalised).
          2. Baseline row (user=None) if the authenticated user has no row.
          3. None if no rows exist at all (AC5 graceful degradation).
        """
        try:
            request = self.context.get("request")
            user = request.user if request and request.user.is_authenticated else None
            stat = school.admission_stats.filter(user=user).first()
            if stat is None and user is not None:
                stat = school.admission_stats.filter(user=None).first()
            if stat is None:
                return None
            return AdmissionStatSerializer(stat, context=self.context).data
        except Exception:
            logger.exception("get_admission_stat failed for school %s", school.slug)
            return None


class ParcoursSerializer(serializers.ModelSerializer):
    """Serializer for Parcours — Story 4.3 graphe parcours par métier.

    Story 4.5: adds nodes_with_stats SerializerMethodField that enriches each
    target/ecole node with an inline admission_stat dict when a matching
    AdmissionStat row exists. Schools are batch-fetched with prefetch_related
    to avoid N+1 queries (AC2).
    """

    target_school_name = serializers.SerializerMethodField()
    target_school_slug = serializers.SerializerMethodField()
    target_school_city = serializers.SerializerMethodField()
    nodes_with_stats = serializers.SerializerMethodField()

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
            "nodes_with_stats",
            "niveau_scolaire",
            "is_default",
            "created_at",
        ]

    def get_target_school_name(self, obj: Parcours) -> str:
        return obj.target_school.name

    def get_target_school_slug(self, obj: Parcours) -> str:
        return obj.target_school.slug

    def get_target_school_city(self, obj: Parcours) -> str:
        return obj.target_school.city

    def get_nodes_with_stats(self, parcours: Parcours) -> list:
        """Enrich target/ecole nodes with inline admission_stat dict (no N+1).

        Story 4.5 AC2: batch-loads all relevant schools + their admission_stats
        in 2 queries (filter + prefetch), then enriches matching nodes in-memory.
        """
        try:
            request = self.context.get("request")
            user = request.user if request and request.user.is_authenticated else None
            school_slugs = [
                n.get("schoolSlug")
                for n in parcours.nodes
                if n.get("schoolSlug") and n.get("type") in ("target", "ecole")
            ]
            schools: dict[str, School] = {}
            if school_slugs:
                schools = {
                    s.slug: s
                    for s in School.objects.filter(slug__in=school_slugs).prefetch_related(
                        "admission_stats"
                    )
                }
            result = []
            for node in parcours.nodes:
                node_copy = dict(node)
                if node.get("type") in ("target", "ecole") and node.get("schoolSlug"):
                    school = schools.get(node["schoolSlug"])
                    if school:
                        user_id = user.id if user else None
                        stat = next(
                            (s for s in school.admission_stats.all() if s.user_id == user_id),
                            None,
                        )
                        if stat is None and user is not None:
                            stat = next(
                                (s for s in school.admission_stats.all() if s.user_id is None),
                                None,
                            )
                        if stat:
                            node_copy["admission_stat"] = {
                                "expected_proba": stat.expected_proba,
                                "label": stat.label,
                                "context_line": stat.context_line,
                                "action_lever": stat.action_lever,
                            }
                result.append(node_copy)
            return result
        except Exception:
            logger.exception("get_nodes_with_stats failed for parcours %s", parcours.id)
            return list(parcours.nodes)
