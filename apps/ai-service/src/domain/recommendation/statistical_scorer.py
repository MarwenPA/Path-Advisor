"""Stub scorer — API contract validation only.

Story 3.3 replaces this with the real statistical + content-based scorer
(passions overlap, valeurs alignment, niveau compatibility, bulletin quality).
"""

from __future__ import annotations

import random

from src.api.schemas import OccupationScore, SignalContributif

MODEL_VERSION = "0.1.0-statistical"
MODEL_TYPE = "statistical_content_based"
FEATURES = ["passions_overlap", "valeurs_alignment", "niveau_compatibility", "bulletin_quality"]


def score_occupations(profile: dict, occupation_ids: list[str]) -> list[OccupationScore]:
    has_bulletins = profile.get("has_bulletins", False)
    confidence: str = "medium" if has_bulletins else "low"
    results = []
    for occ_id in occupation_ids:
        score = random.randint(20, 95)
        results.append(
            OccupationScore(
                occupation_id=occ_id,
                score=score,
                signals_contributifs=[
                    SignalContributif(
                        signal="passions_overlap",
                        weight=0.35,
                        contribution=int(score * 0.35),
                    ),
                    SignalContributif(
                        signal="valeurs_alignment",
                        weight=0.25,
                        contribution=int(score * 0.25),
                    ),
                ],
                confidence_level=confidence,  # type: ignore[arg-type]
            )
        )
    return results
