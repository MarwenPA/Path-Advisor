"""Unit tests for the real statistical content-based scorer.

Tests are deterministic — no random values — and cover the 4 weighted features,
Jaccard similarity, graceful degradation, confidence levels, and edge cases.
"""

from __future__ import annotations

from src.domain.recommendation.statistical_scorer import (
    MODEL_VERSION,
    _bulletin_quality,
    _confidence_level,
    _jaccard,
    _niveau_compatibility,
    _passion_overlap,
    _valeur_alignment,
    score_occupations,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

FULL_PROFILE = {
    "passions": ["biologie", "soins", "bénévolat"],
    "valeurs": ["utilité sociale", "contact humain"],
    "niveau": "terminale_generale",
    "specialites": ["SVT", "Maths"],
    "has_bulletins": True,
    "bulletin_summary": {"average": 16.0, "appreciation_keywords": ["sérieux"]},
}

PROFESSION_SIGNALS = {
    "occupation_id": "occ_infirmier",
    "signals_json": {
        "passions": ["biologie", "aider les autres", "soins"],
        "valeurs": ["utilité sociale", "stabilité"],
        "specialites": ["svt", "chimie"],
        "keywords": ["soin", "hôpital"],
    },
    "level_compatibility": ["terminale_generale", "postbac", "lycee_1ere_tle_general"],
}

# ─── _jaccard ─────────────────────────────────────────────────────────────────


def test_jaccard_empty_sets_returns_zero() -> None:
    assert _jaccard(set(), set()) == 0.0


def test_jaccard_no_overlap() -> None:
    assert _jaccard({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_full_overlap() -> None:
    assert _jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_partial_overlap() -> None:
    # {"biologie"} ∩ {"biologie", "chimie", "sport"} = {"biologie"}
    # union = 3
    result = _jaccard({"biologie"}, {"biologie", "chimie", "sport"})
    assert abs(result - 1 / 3) < 1e-9


def test_jaccard_case_insensitive() -> None:
    result = _jaccard({"Biologie"}, {"biologie"})
    assert result == 1.0


def test_jaccard_strips_whitespace() -> None:
    result = _jaccard({"  biologie  "}, {"biologie"})
    assert result == 1.0


def test_jaccard_one_empty_set() -> None:
    assert _jaccard({"biologie"}, set()) == 0.0


# ─── _passion_overlap ─────────────────────────────────────────────────────────


def test_passion_overlap_known_value() -> None:
    profile = {"passions": ["biologie", "soins", "sport"]}
    signals = {"passions": ["biologie", "aider les autres", "soins"]}
    # intersection: {"biologie","soins"} = 2, union: {"biologie","soins","sport","aider les autres"} = 4
    result = _passion_overlap(profile, signals)
    assert abs(result - 2 / 4) < 1e-9


def test_passion_overlap_empty_profile() -> None:
    result = _passion_overlap({}, {"passions": ["biologie"]})
    assert result == 0.0


def test_passion_overlap_empty_profession() -> None:
    result = _passion_overlap({"passions": ["biologie"]}, {})
    assert result == 0.0


def test_passion_overlap_none_passions() -> None:
    result = _passion_overlap({"passions": None}, {"passions": ["biologie"]})
    assert result == 0.0


# ─── _valeur_alignment ────────────────────────────────────────────────────────


def test_valeur_alignment_known_value() -> None:
    profile = {"valeurs": ["utilité sociale", "autonomie"]}
    signals = {"valeurs": ["utilité sociale", "contact humain"]}
    # intersection: {"utilité sociale"} = 1, union: 3
    result = _valeur_alignment(profile, signals)
    assert abs(result - 1 / 3) < 1e-9


def test_valeur_alignment_empty() -> None:
    assert _valeur_alignment({}, {}) == 0.0


# ─── _niveau_compatibility ────────────────────────────────────────────────────


def test_niveau_compatibility_match() -> None:
    profile = {"niveau": "terminale_generale"}
    assert _niveau_compatibility(profile, ["terminale_generale", "postbac"]) == 1.0


def test_niveau_compatibility_no_match() -> None:
    profile = {"niveau": "college_3eme"}
    assert _niveau_compatibility(profile, ["terminale_generale", "postbac"]) == 0.0


def test_niveau_compatibility_missing_niveau() -> None:
    assert _niveau_compatibility({}, ["terminale_generale"]) == 0.0


def test_niveau_compatibility_empty_list() -> None:
    assert _niveau_compatibility({"niveau": "terminale_generale"}, []) == 0.0


def test_niveau_compatibility_case_insensitive() -> None:
    """Student niveau casing must not affect match (C2 fix)."""
    profile = {"niveau": "Terminale_Generale"}
    assert _niveau_compatibility(profile, ["terminale_generale"]) == 1.0


def test_niveau_compatibility_level_compat_case_insensitive() -> None:
    """level_compatibility entries are also lowercased before comparison."""
    profile = {"niveau": "terminale_generale"}
    assert _niveau_compatibility(profile, ["Terminale_Generale", "Postbac"]) == 1.0


# ─── _bulletin_quality ────────────────────────────────────────────────────────


def test_bulletin_quality_no_bulletins() -> None:
    assert _bulletin_quality({"has_bulletins": False}) == 0.0


def test_bulletin_quality_no_bulletins_default() -> None:
    assert _bulletin_quality({}) == 0.0


def test_bulletin_quality_with_average_16() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": {"average": 16.0}}
    result = _bulletin_quality(profile)
    assert abs(result - 16.0 / 20.0) < 1e-9


def test_bulletin_quality_capped_at_1() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": {"average": 22.0}}
    assert _bulletin_quality(profile) == 1.0


def test_bulletin_quality_missing_summary() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": None}
    assert _bulletin_quality(profile) == 0.5


def test_bulletin_quality_missing_average() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": {"appreciation_keywords": []}}
    assert _bulletin_quality(profile) == 0.5


def test_bulletin_quality_non_numeric_average() -> None:
    """Non-numeric average must not raise — neutral fallback (C4 fix)."""
    profile = {"has_bulletins": True, "bulletin_summary": {"average": "N/A"}}
    assert _bulletin_quality(profile) == 0.5


# ─── _confidence_level ────────────────────────────────────────────────────────


def test_confidence_low_no_bulletins() -> None:
    assert _confidence_level({"has_bulletins": False}) == "low"


def test_confidence_low_default() -> None:
    assert _confidence_level({}) == "low"


def test_confidence_medium_below_14() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": {"average": 12.5}}
    assert _confidence_level(profile) == "medium"


def test_confidence_medium_missing_average() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": None}
    assert _confidence_level(profile) == "medium"


def test_confidence_medium_non_numeric_average() -> None:
    """Non-numeric average must not raise — medium fallback (C4 fix)."""
    profile = {"has_bulletins": True, "bulletin_summary": {"average": "N/A"}}
    assert _confidence_level(profile) == "medium"


def test_confidence_high_at_14() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": {"average": 14.0}}
    assert _confidence_level(profile) == "high"


def test_confidence_high_above_14() -> None:
    profile = {"has_bulletins": True, "bulletin_summary": {"average": 18.0}}
    assert _confidence_level(profile) == "high"


# ─── score_occupations ────────────────────────────────────────────────────────


def test_score_occupations_empty_ids() -> None:
    result = score_occupations(FULL_PROFILE, [], None)
    assert result == []


def test_score_occupations_returns_one_per_id() -> None:
    result = score_occupations(FULL_PROFILE, ["occ_01", "occ_02"], [PROFESSION_SIGNALS])
    assert len(result) == 2
    ids = {o.occupation_id for o in result}
    assert ids == {"occ_01", "occ_02"}


def test_score_occupations_score_in_range() -> None:
    result = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    assert len(result) == 1
    assert 0 <= result[0].score <= 100


def test_score_occupations_deterministic() -> None:
    r1 = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    r2 = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    assert r1[0].score == r2[0].score


def test_score_occupations_known_score() -> None:
    """Verify exact score for fully known profile + profession."""
    profile = {
        "passions": ["biologie"],
        "valeurs": ["utilité sociale"],
        "niveau": "terminale_generale",
        "specialites": [],
        "has_bulletins": True,
        "bulletin_summary": {"average": 20.0},
    }
    profession = {
        "occupation_id": "occ_test",
        "signals_json": {"passions": ["biologie"], "valeurs": ["utilité sociale"]},
        "level_compatibility": ["terminale_generale"],
    }
    result = score_occupations(profile, ["occ_test"], [profession])
    occ = result[0]
    # passion_overlap=1.0, valeur=1.0, niveau=1.0, bulletin=1.0 → 100
    assert occ.score == 100
    assert occ.confidence_level == "high"


def test_score_occupations_no_overlap_gives_low_score() -> None:
    profile = {
        "passions": ["photographie"],
        "valeurs": ["liberté"],
        "niveau": "college_3eme",
        "has_bulletins": False,
    }
    profession = {
        "occupation_id": "occ_infirmier",
        "signals_json": {"passions": ["biologie"], "valeurs": ["utilité sociale"]},
        "level_compatibility": ["terminale_generale"],
    }
    result = score_occupations(profile, ["occ_infirmier"], [profession])
    assert result[0].score == 0
    assert result[0].confidence_level == "low"


def test_score_occupations_four_signals() -> None:
    result = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    signals = result[0].signals_contributifs
    assert len(signals) == 4
    keys = {s.signal for s in signals}
    assert keys == {
        "passion_overlap",
        "valeur_alignment",
        "niveau_compatibility",
        "bulletin_quality",
    }


def test_score_occupations_weights_sum_to_one() -> None:
    result = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    total = sum(s.weight for s in result[0].signals_contributifs)
    assert abs(total - 1.0) < 1e-9


def test_score_occupations_no_professions_data_graceful() -> None:
    """When professions_data is None, scorer uses empty signals (no passion/valeur overlap)."""
    profile = {
        "passions": ["biologie"],
        "valeurs": ["utilité sociale"],
        "niveau": "terminale_generale",
        "has_bulletins": True,
        "bulletin_summary": {"average": 16.0},
    }
    result = score_occupations(profile, ["occ_01"], None)
    occ = result[0]
    # niveau_compat=0 (no level_compat data), bulletin=16/20=0.8 → 0*0.20*100 + 0.8*0.20*100 = 16
    assert occ.score == 16
    assert occ.confidence_level == "high"


def test_score_occupations_clamped_to_100() -> None:
    """Score should never exceed 100."""
    result = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    assert result[0].score <= 100


def test_score_occupations_high_confidence() -> None:
    result = score_occupations(FULL_PROFILE, ["occ_infirmier"], [PROFESSION_SIGNALS])
    assert result[0].confidence_level == "high"  # average=16.0 >= 14.0


def test_model_version_bumped() -> None:
    assert MODEL_VERSION == "0.2.0-statistical"


def test_score_occupations_missing_occupation_id_in_professions_data_is_skipped() -> None:
    """Malformed professions_data entry without occupation_id must not raise (C3 fix)."""
    profile = {
        "passions": ["biologie"],
        "valeurs": ["utilité sociale"],
        "niveau": "terminale_generale",
        "has_bulletins": False,
    }
    bad_entry = {"signals_json": {"passions": ["biologie"]}, "level_compatibility": []}
    result = score_occupations(profile, ["occ_01"], [bad_entry])
    assert len(result) == 1
    assert result[0].occupation_id == "occ_01"
