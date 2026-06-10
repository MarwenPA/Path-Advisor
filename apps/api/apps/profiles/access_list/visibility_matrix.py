"""Visibility matrix — the SINGLE SOURCE OF TRUTH for "what does tier X see".

Story 1.9 §AC3 / §T2. Every source adapter reads from this dict ; NEVER
inline the lists into the adapter. When Story 6.3 (confidentiality frontier)
changes what a parent sees, this one file changes.

Data-area names are the canonical short-form identifiers — keep them stable.
Both the API JSON ``visible_data`` / ``masked_data`` lists and any future
filtering layer (RBAC field-level, GraphQL scopes) reference these strings.
"""

from __future__ import annotations

from .dto import TierType

#: Canonical data areas. Adding a new area = add a new entry to EVERY tier
#: (visible or masked) and update the test ``test_visibility_matrix.py``.
KNOWN_DATA_AREAS: frozenset[str] = frozenset(
    {
        "metiers_explores",
        "parcours_sauvegardes",
        "recommandations",
        "parcoursup_voeux",
        "bulletins_detailles",
        "appreciations_enseignants",
        "motivation_libre",
    }
)


#: Per-tier visibility. ``visible`` + ``masked`` MUST partition KNOWN_DATA_AREAS
#: (no overlap, no leftover) — enforced by ``test_visibility_matrix.py``.
VISIBILITY_MATRIX: dict[TierType, dict[str, tuple[str, ...]]] = {
    # FR41 — parents see exploration trace + saved paths only. Bulletins,
    # comments, free-form motivation stay masked (PRD §Confidentialité parent).
    "parent": {
        "visible": ("metiers_explores", "parcours_sauvegardes"),
        "masked": (
            "recommandations",
            "parcoursup_voeux",
            "bulletins_detailles",
            "appreciations_enseignants",
            "motivation_libre",
        ),
    },
    # Story 5.4 — école partenaire receives the OUTREACH profile snapshot
    # (recommandations + parcoursup_voeux + motivation_libre — what the student
    # CHOSE to share). They never see exploration or raw bulletins.
    "school": {
        "visible": ("recommandations", "parcoursup_voeux", "motivation_libre"),
        "masked": (
            "metiers_explores",
            "parcours_sauvegardes",
            "bulletins_detailles",
            "appreciations_enseignants",
        ),
    },
    # Story 6.7/6.8 — conseillère sees the FULL profile minus the free-form
    # motivation (which goes only to the école the student applies to).
    "counselor": {
        "visible": (
            "metiers_explores",
            "parcours_sauvegardes",
            "recommandations",
            "parcoursup_voeux",
            "bulletins_detailles",
            "appreciations_enseignants",
        ),
        "masked": ("motivation_libre",),
    },
}
