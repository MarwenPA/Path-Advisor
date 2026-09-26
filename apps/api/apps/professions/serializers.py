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


class ProfessionPublicSeoSerializer(serializers.ModelSerializer):
    """Fields exposed to ANONYMOUS visitors — Story 7.1 (SEO SSR fiches
    métier). Includes `signals_json` — despite the name, these are
    descriptive keyword tags ("quelles passions/valeurs correspondent à ce
    métier"), not a scoring secret, and `<FicheMetier>`'s "Signaux" tab +
    hero chips unconditionally read this field — omitting it would break
    rendering, not just hide internals. Excludes only `id`/`is_active`
    (internal PK/flag, never rendered — confirmed via a repo-wide grep for
    `profession.id` in the professions component tree, zero hits).
    """

    class Meta:
        model = Profession
        fields = [
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
        ]
        read_only_fields = fields


class ProfessionSlugSerializer(serializers.ModelSerializer):
    """Minimal `{slug, updated_at}` rows for `/sitemap.xml` — Story 7.4.
    Deliberately not the full catalog serializer: a sitemap generator needs
    nothing but the URL-building key + `lastmod`.
    """

    class Meta:
        model = Profession
        fields = ["slug", "updated_at"]
        read_only_fields = fields


class ProfessionCatalogSerializer(serializers.ModelSerializer):
    """Lightweight fields for the catalog LIST view — Story 3.13.

    Deliberately excludes `daily_routine`/`requirements_json`/
    `prospects_text`/`signals_json`: unnecessary payload weight for a list
    of 50+ cards, and already served in full by `ProfessionPublicSerializer`
    on the existing detail endpoint (`/metiers/{slug}`, unchanged).
    """

    class Meta:
        model = Profession
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "sector",
            "median_salary_eur",
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
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProfessionAdminWriteSerializer(serializers.ModelSerializer):
    """Story 9.1 — create/update payload for the back-office CRUD.

    Validates the JSON shapes the rest of the product depends on — above
    all `signals_json`: the 8.5 digest and the 8.6 DeltaRecap match on its
    three list dimensions, so a malformed shape here would silently break
    the matching for every student.
    """

    class Meta:
        model = Profession
        fields = [
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
            "status",
        ]

    def validate_signals_json(self, value: dict) -> dict:
        if not isinstance(value, dict):
            raise serializers.ValidationError("signals_json doit être un objet JSON.")
        for key in ("passions", "valeurs", "specialites"):
            entries = value.get(key, [])
            if not isinstance(entries, list) or not all(isinstance(x, str) for x in entries):
                raise serializers.ValidationError(
                    f"signals_json.{key} doit être une liste de chaînes "
                    "(le matching 8.5/8.6 repose sur ces trois dimensions)."
                )
        return value

    def validate_level_compatibility(self, value: list) -> list:
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise serializers.ValidationError(
                "level_compatibility doit être une liste de niveaux (chaînes)."
            )
        return value

    def validate_requirements_json(self, value: list) -> list:
        if not isinstance(value, list):
            raise serializers.ValidationError("requirements_json doit être une liste.")
        for entry in value:
            if not isinstance(entry, dict) or "label" not in entry:
                raise serializers.ValidationError(
                    'Chaque prérequis doit être un objet avec au moins "label".'
                )
        return value

    def validate_sources_json(self, value: list) -> list:
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise serializers.ValidationError("sources_json doit être une liste de chaînes.")
        return value


class ProfessionRevisionSerializer(serializers.ModelSerializer):
    """Story 9.1 — history panel rows."""

    editor_email = serializers.SerializerMethodField()
    restored_from_id = serializers.CharField(source="restored_from.id", default=None)

    class Meta:
        from apps.professions.models import ProfessionRevision

        model = ProfessionRevision
        fields = ["id", "action", "snapshot", "editor_email", "restored_from_id", "created_at"]
        read_only_fields = fields

    def get_editor_email(self, obj) -> str | None:
        return obj.editor.email if obj.editor else None
