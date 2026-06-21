"""Statistical content-based scorer — Story 3.3, updated Story 3.9.

5-feature scoring model (v0.3):
  - passion_overlap      (30%) — Jaccard similarity on passion sets
  - valeur_alignment     (20%) — Jaccard similarity on value sets
  - niveau_compatibility (15%) — Binary: student level ∈ profession.level_compatibility
  - specialite_overlap   (15%) — Jaccard similarity on specialite sets (Story 3.9)
  - bulletin_quality     (20%) — Grade percentile; 0 if no bulletins

All helpers are module-level so they can be tested in isolation.
"""

from __future__ import annotations

from typing import Literal

from src.api.schemas import OccupationScore, SignalContributif

MODEL_VERSION = "0.3.0-statistical"
MODEL_TYPE = "statistical_content_based"
FEATURES = [
    "passion_overlap",
    "valeur_alignment",
    "niveau_compatibility",
    "specialite_overlap",
    "bulletin_quality",
]

_WEIGHTS: dict[str, float] = {
    "passion_overlap": 0.30,
    "valeur_alignment": 0.20,
    "niveau_compatibility": 0.15,
    "specialite_overlap": 0.15,
    "bulletin_quality": 0.20,
}


# ─── Feature helpers ──────────────────────────────────────────────────────────


def _jaccard(a: set[str], b: set[str]) -> float:
    """Normalized Jaccard similarity — case-insensitive, stripped."""
    na = {s.lower().strip() for s in a}
    nb = {s.lower().strip() for s in b}
    union = na | nb
    if not union:
        return 0.0
    return len(na & nb) / len(union)


def _passion_overlap(profile: dict, signals: dict) -> float:
    return _jaccard(
        set(profile.get("passions") or []),
        set(signals.get("passions") or []),
    )


def _valeur_alignment(profile: dict, signals: dict) -> float:
    return _jaccard(
        set(profile.get("valeurs") or []),
        set(signals.get("valeurs") or []),
    )


def _niveau_compatibility(profile: dict, level_compatibility: list[str]) -> float:
    niveau = (profile.get("niveau") or "").strip().lower()
    if not niveau or not level_compatibility:
        return 0.0
    normalized = {lc.lower().strip() for lc in level_compatibility}
    return 1.0 if niveau in normalized else 0.0


def _specialite_overlap(profile: dict, signals: dict) -> float:
    """Jaccard similarity between student specialites and profession required specialites."""
    return _jaccard(
        set(profile.get("specialites") or []),
        set(signals.get("specialites") or []),
    )


def _bulletin_quality(profile: dict) -> float:
    if not profile.get("has_bulletins"):
        return 0.0
    bs = profile.get("bulletin_summary") or {}
    avg = bs.get("average") if isinstance(bs, dict) else None
    if avg is None:
        return 0.5  # neutral fallback for missing grade
    try:
        return min(float(avg) / 20.0, 1.0)
    except (TypeError, ValueError):
        return 0.5


def _confidence_level(profile: dict) -> Literal["low", "medium", "high"]:
    if not profile.get("has_bulletins"):
        return "low"
    bs = profile.get("bulletin_summary") or {}
    avg = bs.get("average") if isinstance(bs, dict) else None
    if avg is None:
        return "medium"
    try:
        avg_float = float(avg)
    except (TypeError, ValueError):
        return "medium"
    return "high" if avg_float >= 14.0 else "medium"


# ─── Main scoring function ────────────────────────────────────────────────────


def score_occupations(
    profile: dict,
    occupation_ids: list[str],
    professions_data: list[dict] | None = None,
) -> list[OccupationScore]:
    """Score a list of occupations against a student profile.

    Args:
        profile: StudentProfile.model_dump() from the request.
        occupation_ids: Opaque occupation identifiers to score.
        professions_data: Optional list of profession signal dicts
            (each with occupation_id, signals_json, level_compatibility).
            When None, passion/valeur/specialite overlap defaults to 0.

    Returns:
        One OccupationScore per occupation_id.
    """
    if not occupation_ids:
        return []

    # Build lookup by occupation_id for O(1) access; skip entries missing occupation_id
    signals_by_id: dict[str, dict] = {}
    if professions_data:
        for p in professions_data:
            occ_id = p.get("occupation_id")
            if occ_id:
                signals_by_id[occ_id] = p

    confidence = _confidence_level(profile)
    f_bulletin = _bulletin_quality(profile)

    results: list[OccupationScore] = []
    for occ_id in occupation_ids:
        profession = signals_by_id.get(occ_id, {})
        signals = profession.get("signals_json", {})
        level_compat: list[str] = profession.get("level_compatibility", [])

        f_passion = _passion_overlap(profile, signals)
        f_valeur = _valeur_alignment(profile, signals)
        f_niveau = _niveau_compatibility(profile, level_compat)
        f_specialite = _specialite_overlap(profile, signals)

        raw_contributions = [
            f_passion * _WEIGHTS["passion_overlap"] * 100,
            f_valeur * _WEIGHTS["valeur_alignment"] * 100,
            f_niveau * _WEIGHTS["niveau_compatibility"] * 100,
            f_specialite * _WEIGHTS["specialite_overlap"] * 100,
            f_bulletin * _WEIGHTS["bulletin_quality"] * 100,
        ]
        # Single round on the summed raw to avoid per-contribution rounding divergence (C1)
        final_score = max(0, min(100, round(sum(raw_contributions))))

        results.append(
            OccupationScore(
                occupation_id=occ_id,
                score=final_score,
                signals_contributifs=[
                    SignalContributif(
                        signal="passion_overlap",
                        weight=_WEIGHTS["passion_overlap"],
                        contribution=round(raw_contributions[0]),
                    ),
                    SignalContributif(
                        signal="valeur_alignment",
                        weight=_WEIGHTS["valeur_alignment"],
                        contribution=round(raw_contributions[1]),
                    ),
                    SignalContributif(
                        signal="niveau_compatibility",
                        weight=_WEIGHTS["niveau_compatibility"],
                        contribution=round(raw_contributions[2]),
                    ),
                    SignalContributif(
                        signal="specialite_overlap",
                        weight=_WEIGHTS["specialite_overlap"],
                        contribution=round(raw_contributions[3]),
                    ),
                    SignalContributif(
                        signal="bulletin_quality",
                        weight=_WEIGHTS["bulletin_quality"],
                        contribution=round(raw_contributions[4]),
                    ),
                ],
                confidence_level=confidence,
            )
        )
    return results
