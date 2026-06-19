"""Fuzzy subject mapper tests — Story 2.3 T5 (backend)."""

import pytest

from apps.bulletins.fuzzy_subject_mapper import map_subject


class TestFuzzyMapper:
    def test_exact_match(self):
        result = map_subject("Mathématiques")
        assert result["unmapped"] is False
        assert result["canonical_id"] is not None

    def test_case_insensitive(self):
        result = map_subject("mathématiques")
        assert result["unmapped"] is False

    def test_close_typo(self):
        # "Mathematiques" (no accent) — distance 1
        result = map_subject("Mathematiques")
        assert result["unmapped"] is False

    def test_unknown_subject_unmapped(self):
        result = map_subject("Klingon Linguistics")
        assert result["unmapped"] is True
        assert result["raw"] == "Klingon Linguistics"

    def test_abbreviated_francais(self):
        result = map_subject("Fr.")
        # Too short / ambiguous — may or may not map, but must not crash
        assert "unmapped" in result

    def test_histoire_geo_variant(self):
        result = map_subject("Hist-Géo")
        assert result["unmapped"] is False

    def test_returns_raw_always(self):
        result = map_subject("Some subject")
        assert "raw" in result
        assert result["raw"] == "Some subject"
