"""Unit tests for the onboarding referentials (Story 2.1 T1).

Pure-module tests: no Django DB, no settings dependency. Run with `pytest`.

Also enforces cross-language ID sync with the TypeScript source of truth at
`apps/web/src/lib/onboarding/referentials.ts` so any drift trips CI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from apps.students.onboarding.referentials import (
    CUSTOM_PASSION_PREFIX,
    MAX_CUSTOM_PASSIONS,
    MAX_PASSIONS_TOTAL,
    PASSION_IDS,
    VALEUR_IDS,
    is_valid_passion_id,
    is_valid_valeur_id,
    validate_interets_record,
    validate_passions_array,
    validate_valeurs_array,
)

# Repo root resolved from this file:
# apps/api/apps/students/tests/test_referentials.py
# parents[0]=tests, [1]=students, [2]=apps (django apps dir), [3]=api, [4]=apps (monorepo apps dir), [5]=repo root.
REPO_ROOT = Path(__file__).resolve().parents[5]
TS_REFERENTIALS = REPO_ROOT / "apps" / "web" / "src" / "lib" / "onboarding" / "referentials.ts"


class TestPassionIDs:
    def test_ships_20_passions(self) -> None:
        assert len(PASSION_IDS) == 20

    def test_unique(self) -> None:
        assert len(set(PASSION_IDS)) == len(PASSION_IDS)

    def test_all_kebab_case(self) -> None:
        for pid in PASSION_IDS:
            assert re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", pid), f"bad id: {pid!r}"


class TestValeurIDs:
    def test_ships_12_valeurs(self) -> None:
        assert len(VALEUR_IDS) == 12

    def test_unique(self) -> None:
        assert len(set(VALEUR_IDS)) == len(VALEUR_IDS)


class TestIsValidPassionID:
    def test_accepts_known_id(self) -> None:
        assert is_valid_passion_id("sciences-nature")

    def test_accepts_valid_custom(self) -> None:
        assert is_valid_passion_id("custom:graphql")
        assert is_valid_passion_id("custom:justice-clima")

    def test_rejects_unknown_bare(self) -> None:
        assert not is_valid_passion_id("unicorns")

    @pytest.mark.parametrize(
        "bad",
        ["custom:Avec Espaces", "custom:-leading", "custom:trailing-", "custom:", "custom:" + "a" * 31],
    )
    def test_rejects_bad_custom_slug(self, bad: str) -> None:
        assert not is_valid_passion_id(bad)

    def test_rejects_non_string(self) -> None:
        assert not is_valid_passion_id(None)  # type: ignore[arg-type]
        assert not is_valid_passion_id(42)  # type: ignore[arg-type]


class TestIsValidValeurID:
    def test_accepts_known(self) -> None:
        assert is_valid_valeur_id("justice-sociale")

    def test_rejects_unknown(self) -> None:
        assert not is_valid_valeur_id("bogus")
        assert not is_valid_valeur_id("custom:patience")


class TestValidatePassionsArray:
    def test_accepts_8(self) -> None:
        ok, err = validate_passions_array(list(PASSION_IDS[:MAX_PASSIONS_TOTAL]))
        assert ok, err

    def test_rejects_9(self) -> None:
        ok, _ = validate_passions_array(list(PASSION_IDS[: MAX_PASSIONS_TOTAL + 1]))
        assert not ok

    def test_rejects_6_customs(self) -> None:
        too_many = [f"{CUSTOM_PASSION_PREFIX}c{i}" for i in range(MAX_CUSTOM_PASSIONS + 1)]
        ok, _ = validate_passions_array(too_many)
        assert not ok

    def test_rejects_duplicates(self) -> None:
        ok, _ = validate_passions_array(["musique", "musique"])
        assert not ok

    def test_rejects_unknown_id(self) -> None:
        ok, _ = validate_passions_array(["sciences-nature", "bogus-id"])
        assert not ok


class TestValidateValeursArray:
    def test_accepts_3(self) -> None:
        ok, err = validate_valeurs_array(["justice-sociale", "creativite", "sens-utilite"])
        assert ok, err

    def test_rejects_6(self) -> None:
        ok, _ = validate_valeurs_array(list(VALEUR_IDS[:6]))
        assert not ok

    def test_rejects_duplicates(self) -> None:
        ok, _ = validate_valeurs_array(["aventure", "aventure", "defi"])
        assert not ok


class TestValidateInteretsRecord:
    def test_accepts_all_null(self) -> None:
        ok, err = validate_interets_record({"1": None, "2": None, "3": None})
        assert ok, err

    def test_accepts_mixed(self) -> None:
        ok, err = validate_interets_record({"1": "Podcast Choses à savoir", "2": None, "3": "TP SVT"})
        assert ok, err

    def test_rejects_long_string(self) -> None:
        ok, _ = validate_interets_record({"1": "a" * 201, "2": None, "3": None})
        assert not ok

    def test_rejects_missing_keys(self) -> None:
        ok, _ = validate_interets_record({"1": None, "2": None})  # type: ignore[arg-type]
        assert not ok


class TestCrossLanguageSync:
    """Guarantee that the Python referential and the TypeScript referential ship
    the SAME IDs. If they drift, the front and back will disagree on what's valid.
    """

    @pytest.fixture
    def ts_content(self) -> str:
        assert TS_REFERENTIALS.exists(), f"TS source missing: {TS_REFERENTIALS}"
        return TS_REFERENTIALS.read_text(encoding="utf-8")

    @staticmethod
    def _extract_ids(ts_content: str, array_name: str) -> list[str]:
        """Parse `{ id: "foo-bar", ... }` entries inside `export const ARRAY: ...`.

        Conservative regex: anchors on the array declaration then captures
        every `id: "..."` inside it until the closing `] as const`.
        """
        start = ts_content.find(f"export const {array_name}")
        assert start != -1, f"array {array_name} not found in TS"
        end = ts_content.find("] as const", start)
        assert end != -1, f"closing `] as const` not found after {array_name}"
        block = ts_content[start:end]
        return re.findall(r'\bid:\s*"([a-z0-9][a-z0-9-]*)"', block)

    def test_passion_ids_match(self, ts_content: str) -> None:
        ts_ids = self._extract_ids(ts_content, "PASSIONS_CATEGORIES")
        assert tuple(ts_ids) == PASSION_IDS, (
            "Frontend and backend passions referentials disagree. "
            f"\nTS:  {ts_ids}\nPY:  {list(PASSION_IDS)}"
        )

    def test_valeur_ids_match(self, ts_content: str) -> None:
        ts_ids = self._extract_ids(ts_content, "VALEURS")
        assert tuple(ts_ids) == VALEUR_IDS, (
            "Frontend and backend valeurs referentials disagree. "
            f"\nTS:  {ts_ids}\nPY:  {list(VALEUR_IDS)}"
        )

    def test_ts_constants_match(self, ts_content: str) -> None:
        """Sanity: the numeric constants on both sides must match too."""
        for py_const, ts_token, py_value in [
            ("MAX_PASSIONS_TOTAL", "MAX_PASSIONS_TOTAL = 8", MAX_PASSIONS_TOTAL),
            ("MAX_CUSTOM_PASSIONS", "MAX_CUSTOM_PASSIONS = 5", MAX_CUSTOM_PASSIONS),
        ]:
            assert ts_token in ts_content, f"{py_const}={py_value} not mirrored as `{ts_token}` in TS"
