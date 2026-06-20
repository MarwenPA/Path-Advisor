"""Tests for Profession schema, seed data invariants, and curation ethics — Story 3.2 T4.

Covers:
- AC1: schema columns present
- AC2: 50+ métiers, sector distribution
- AC3: quality invariants per profession (word counts, JSON field minimums)
- AC4: ethical curation (bac-pro ≥30%, college_3eme ≥30%, sector diversity)
- AC5: sources traceability
"""

from __future__ import annotations

import pytest

from apps.professions.management.commands.seed_professions import ALL_PROFESSIONS as ALL_SEED_DATA

# ── AC2 sector semantic mapping ───────────────────────────────────────────────
# Maps AC2 table categories (story §AC2) to `sector` field values used in seed.
AC2_SECTOR_GROUPS: dict[str, list[str]] = {
    "santé_social": ["santé", "social"],
    "sciences_tech_industrie": ["sciences", "tech", "industrie"],
    "btp_artisanat": ["btp", "industrie"],
    "business_commerce": ["business"],
    "arts_culture": ["arts"],
    "environnement_agriculture": ["environnement"],
    "enseignement_formation": ["enseignement"],
    "securite_defense": ["securite"],
    "transport_logistique": ["transport"],
}

AC2_MINIMUMS: dict[str, int] = {
    "santé_social": 8,
    "sciences_tech_industrie": 8,
    "btp_artisanat": 6,
    "business_commerce": 6,
    "arts_culture": 6,
    "environnement_agriculture": 4,
    "enseignement_formation": 4,
    "securite_defense": 4,
    "transport_logistique": 4,
}

VALID_LEVELS = {
    "college_3eme",
    "lycee_2nde",
    "lycee_1ere_tle_general",
    "lycee_1ere_tle_techno",
    "lycee_1ere_tle_pro",
    "postbac",
}

VALID_SOURCES = {
    "Onisep 2025",
    "ROME v4.0",
    "Apec 2025",
    "France Travail 2025",
    "validation humaine 2026-06",
}


# ── AC1: Schema via model ─────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_profession_model_fields_exist():
    """AC1: Profession model exposes all required columns."""
    from apps.professions.models import Profession

    expected_fields = {
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
    }
    model_fields = {f.name for f in Profession._meta.get_fields()}
    assert expected_fields.issubset(model_fields), (
        f"Missing fields: {expected_fields - model_fields}"
    )


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_profession_gin_indexes_exist():
    """AC1: GIN indexes present on signals_json and level_compatibility."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'professions_profession';"
        )
        indexes = {row[0] for row in cursor.fetchall()}

    assert "professions_signals_json_gin" in indexes, "Missing GIN index on signals_json"
    assert "professions_level_compat_gin" in indexes, "Missing GIN index on level_compatibility"


# ── AC2: Seed coverage ────────────────────────────────────────────────────────


def test_seed_slugs_are_unique():
    """Seed data: no duplicate slugs across _seed_data_part1/2/3."""
    slugs = [p["slug"] for p in ALL_SEED_DATA]
    duplicates = [s for s in set(slugs) if slugs.count(s) > 1]
    assert not duplicates, f"Duplicate slugs in seed data: {duplicates}"


class TestSeedCoverage:
    """AC2: 50+ active professions, sector distribution."""

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_at_least_50_active_professions(self, loaded_seed):
        from apps.professions.models import Profession

        count = Profession.objects.filter(is_active=True).count()
        assert count >= 50, f"Expected ≥50 active professions, got {count}"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_mehdi_compatible_professions(self, loaded_seed):
        """AC2: ≥15 professions compatible with college_3eme or lycee_1ere_tle_pro."""
        from apps.professions.models import Profession

        mehdi_qs = Profession.objects.filter(is_active=True).filter(
            level_compatibility__overlap=["college_3eme", "lycee_1ere_tle_pro"]
        )
        assert mehdi_qs.count() >= 15, (
            f"Expected ≥15 Mehdi-compatible professions, got {mehdi_qs.count()}"
        )

    def test_seed_data_sector_minimums(self):
        """AC2: Each AC2 category reaches its minimum (data-level check, no DB)."""
        for category, sectors in AC2_SECTOR_GROUPS.items():
            count = sum(1 for p in ALL_SEED_DATA if p["sector"] in sectors)
            minimum = AC2_MINIMUMS[category]
            assert count >= minimum, f"Sector '{category}' has {count} professions, need ≥{minimum}"


# ── AC3: Quality invariants ───────────────────────────────────────────────────


class TestQualityInvariants:
    """AC3: Per-profession field quality checks on seed data."""

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_description_word_count(self, profession):
        """AC3: description 100-300 words."""
        words = len(profession["description"].split())
        assert 100 <= words <= 300, (
            f"{profession['slug']}: description has {words} words (need 100-300)"
        )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_daily_routine_word_count(self, profession):
        """AC3: daily_routine 80-200 words."""
        words = len(profession["daily_routine"].split())
        assert 80 <= words <= 200, (
            f"{profession['slug']}: daily_routine has {words} words (need 80-200)"
        )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_daily_routine_second_person(self, profession):
        """AC3: daily_routine is written in second person (uses 'tu'/'ta'/'ton')."""
        routine = profession["daily_routine"].lower()
        has_second_person = (
            " tu " in routine
            or routine.startswith("tu ")
            or " ta " in routine
            or routine.startswith("ta ")
        )
        assert has_second_person, (
            f"{profession['slug']}: daily_routine must be in second person (use 'tu'/'ta')"
        )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_requirements_json_minimum_5_items(self, profession):
        """AC3: requirements_json ≥ 5 items."""
        reqs = profession["requirements_json"]
        assert len(reqs) >= 5, (
            f"{profession['slug']}: requirements_json has {len(reqs)} items (need ≥5)"
        )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_requirements_json_has_type_and_label(self, profession):
        """AC3: each requirement has type and label keys."""
        for item in profession["requirements_json"]:
            assert "type" in item and "label" in item, (
                f"{profession['slug']}: requirement missing 'type' or 'label': {item}"
            )
            assert item["type"] in ("studies", "skill", "quality"), (
                f"{profession['slug']}: unknown requirement type '{item['type']}'"
            )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_signals_json_minimum_8_items(self, profession):
        """AC3: signals_json total keywords ≥ 8."""
        sig = profession["signals_json"]
        total = sum(len(v) for v in sig.values() if isinstance(v, list))
        assert total >= 8, f"{profession['slug']}: signals_json has {total} keywords (need ≥8)"

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_signals_json_has_required_keys(self, profession):
        """AC3: signals_json has passions, valeurs, specialites, keywords."""
        sig = profession["signals_json"]
        for key in ("passions", "valeurs", "specialites", "keywords"):
            assert key in sig, f"{profession['slug']}: signals_json missing key '{key}'"

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_level_compatibility_not_empty(self, profession):
        """AC3: level_compatibility has at least 1 entry."""
        assert len(profession["level_compatibility"]) >= 1, (
            f"{profession['slug']}: level_compatibility is empty"
        )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_level_compatibility_valid_values(self, profession):
        """AC3: all level_compatibility values are valid."""
        for level in profession["level_compatibility"]:
            assert level in VALID_LEVELS, f"{profession['slug']}: invalid level '{level}'"

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_prospects_text_at_least_3_items(self, profession):
        """AC3: prospects_text must describe at least 3 career evolution paths."""
        import re

        prospects = profession["prospects_text"]
        count = len(re.findall(r"\d+\.", prospects))
        assert count >= 3, (
            f"{profession['slug']}: prospects_text has {count} numbered items (need ≥3)"
        )

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_no_critical_fields_empty(self, profession):
        """AC3: no critical field is empty."""
        for field in ("name", "description", "daily_routine", "prospects_text"):
            assert profession[field].strip(), f"{profession['slug']}: field '{field}' is empty"


# ── AC4: Ethical curation ─────────────────────────────────────────────────────


class TestEthicalCuration:
    """AC4: Equity of profiles (bac pro ≥30%, college_3eme ≥30%, sector diversity)."""

    def test_bac_pro_at_least_30_percent(self):
        """AC4: ≥30% of professions include lycee_1ere_tle_pro."""
        bac_pro = [p for p in ALL_SEED_DATA if "lycee_1ere_tle_pro" in p["level_compatibility"]]
        ratio = len(bac_pro) / len(ALL_SEED_DATA)
        assert ratio >= 0.30, (
            f"Bac pro professions: {len(bac_pro)}/{len(ALL_SEED_DATA)} = {ratio:.1%} (need ≥30%)"
        )

    def test_college_3eme_at_least_30_percent(self):
        """AC4: ≥30% of professions include college_3eme."""
        college = [p for p in ALL_SEED_DATA if "college_3eme" in p["level_compatibility"]]
        ratio = len(college) / len(ALL_SEED_DATA)
        assert ratio >= 0.30, (
            f"3ème professions: {len(college)}/{len(ALL_SEED_DATA)} = {ratio:.1%} (need ≥30%)"
        )

    def test_bac_pro_covers_at_least_5_sectors(self):
        """AC4: bac-pro compatible professions span at least 5 different sectors."""
        bac_pro = [p for p in ALL_SEED_DATA if "lycee_1ere_tle_pro" in p["level_compatibility"]]
        sectors = {p["sector"] for p in bac_pro}
        assert len(sectors) >= 5, f"Bac pro covers only {len(sectors)} sectors: {sectors} (need ≥5)"


# ── AC5: Sources traceability ─────────────────────────────────────────────────


class TestSources:
    """AC5: Each profession has at least one recognised source."""

    @pytest.mark.parametrize("profession", ALL_SEED_DATA, ids=[p["slug"] for p in ALL_SEED_DATA])
    def test_at_least_one_valid_source(self, profession):
        """AC5: sources_json includes at least one recognised source."""
        sources = profession.get("sources_json", [])
        assert sources, f"{profession['slug']}: sources_json is empty"
        recognised = [s for s in sources if any(valid in s for valid in VALID_SOURCES)]
        assert recognised, f"{profession['slug']}: no recognised source in {sources}"


# ── DB-level fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def loaded_seed(db):
    """Load the full seed into the test DB."""
    from apps.professions.models import Profession

    for data in ALL_SEED_DATA:
        Profession.objects.update_or_create(
            slug=data["slug"],
            defaults={k: v for k, v in data.items() if k != "slug"},
        )
    return None
