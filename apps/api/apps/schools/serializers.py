"""Serializers for the Schools & Formations referential — Story 4.1 / 4.2 / 4.3 / 4.5 / 4.6 / 4.7."""

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


class SchoolCatalogSerializer(serializers.ModelSerializer):
    """Lightweight fields for the catalog LIST view — mirrors
    `ProfessionCatalogSerializer` (Story 3.13): no `formations`/
    `admission_stat` (per-school N+1 / user-specific — detail-only,
    unchanged on `/schools/{slug}`), just enough for a card grid.
    """

    class Meta:
        model = School
        fields = (
            "id",
            "slug",
            "name",
            "type",
            "city",
            "region",
            "selectivity_index",
        )
        read_only_fields = fields


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


class SchoolPublicSeoSerializer(serializers.ModelSerializer):
    """Fields exposed to ANONYMOUS visitors — Story 7.2 (SEO SSR fiches
    école/formation). No `admission_stat` field at all — AC2 requires
    "sélectivité brute (anonyme, pas personnalisée)", not the
    personalized-or-baseline probability `SchoolDetailSerializer` resolves
    via `get_admission_stat`. `selectivity_index` (a plain 1-5 star rating,
    not a computed probability) stays — that IS the "brute" figure the AC
    asks for. No `id` (internal PK, never rendered by `<FicheEcole>`).
    """

    formations = FormationInlineSerializer(many=True, read_only=True)
    metiers_cibles = serializers.SerializerMethodField()
    similar_schools = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = (
            "slug",
            "name",
            "type",
            "city",
            "region",
            "postal_code",
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
            "metiers_cibles",
            "similar_schools",
        )
        read_only_fields = fields

    def get_metiers_cibles(self, school: School) -> list[dict]:
        """AC2 cross-linking — "liens internes vers les métiers cible".

        No FK from `School`/`top_debouches` (free-text strings) to
        `Profession` exists — best-effort case-insensitive name match
        against the profession catalog. Unmatched `top_debouches` entries
        are simply omitted here (still rendered as plain text by the
        frontend from `top_debouches` itself); documented limitation, not
        a silent data loss (nothing is hidden — the frontend has the raw
        list too).
        """
        from apps.professions.models import Profession

        if not school.top_debouches:
            return []
        wanted_lower = {n.lower() for n in school.top_debouches}
        matches = Profession.objects.filter(is_active=True).values("slug", "name")
        return [m for m in matches if m["name"].lower() in wanted_lower][:10]

    def get_similar_schools(self, school: School) -> list[dict]:
        """AC2 cross-linking — "écoles similaires". No similarity/
        recommendation model exists — heuristic: same `type`, excluding
        self, ordered by name, capped at 4. Documented as a proxy, not a
        real similarity engine.
        """
        similar = (
            School.objects.filter(type=school.type)
            .exclude(id=school.id)
            .order_by("name")
            .values("slug", "name", "city")[:4]
        )
        return list(similar)


class ParcoursPublicSeoSerializer(serializers.ModelSerializer):
    """Fields exposed to ANONYMOUS visitors — Story 7.3 (landing pages
    long-tail SEO, "Quels bacs / formations choisir ?" panel + "écoles
    cibles"). Deliberately narrower than `ParcoursSerializer`: no
    `nodes`/`edges` (the full interactive graph — too heavy for a text
    landing page) and no personalized `admission_stat` per node — this is
    "quel bac mène à quelle école", not "mes chances à cette école".
    """

    target_school_name = serializers.SerializerMethodField()
    target_school_slug = serializers.SerializerMethodField()
    target_school_city = serializers.SerializerMethodField()

    class Meta:
        model = Parcours
        fields = [
            "niveau_scolaire",
            "label",
            "is_default",
            "target_school_name",
            "target_school_slug",
            "target_school_city",
        ]
        read_only_fields = fields

    def get_target_school_name(self, obj: Parcours) -> str | None:
        return obj.target_school.name if obj.target_school else None

    def get_target_school_slug(self, obj: Parcours) -> str | None:
        return obj.target_school.slug if obj.target_school else None

    def get_target_school_city(self, obj: Parcours) -> str | None:
        return obj.target_school.city if obj.target_school else None


class ParcoursSerializer(serializers.ModelSerializer):
    """Serializer for Parcours — Story 4.3 + 4.5 inline stats + 4.6 filter metadata + 4.7 dates.

    Story 4.3: base fields (profession, target_school, nodes, edges, niveau_scolaire, is_default).
    Story 4.5: adds nodes_with_stats SerializerMethodField that enriches each target/ecole node
    with an inline admission_stat dict when a matching AdmissionStat row exists.
    Schools are batch-fetched with prefetch_related to avoid N+1 queries (AC2).
    Story 4.6: denormalized filter metadata (tuition_max, selectivity, apprenticeship, internship)
    so the front-end can apply client-side filtering without extra round-trips.
    Story 4.7: label field, target_school_affelnet_dates, target_school_parcoursup_dates for
    admission date display per niveau scolaire.
    """

    target_school_name = serializers.SerializerMethodField()
    target_school_slug = serializers.SerializerMethodField()
    target_school_city = serializers.SerializerMethodField()
    nodes_with_stats = serializers.SerializerMethodField()
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
            "nodes_with_stats",
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
