"""Onboarding step-2 referentials — niveau scolaire, filières, spécialités.

IDs are kebab-case and stored verbatim in the database. Labels are display-only.
The `REF_VERSION` is stored server-side for audit longitudinal (Story 2.2 §T1).

MIRROR: keep in sync with `apps/web/src/lib/onboarding/levels.ts`.
The `test_levels_sync` pytest enforces ID equality across both sides.
"""

from __future__ import annotations

REF_VERSION = "2026-05-v1"

# ---------------------------------------------------------------------------
# Niveau scolaire IDs
# ---------------------------------------------------------------------------

NIVEAU_IDS: frozenset[str] = frozenset(
    [
        "college_3eme",
        "lycee_2nde",
        "lycee_1ere",
        "lycee_terminale",
        "postbac",
    ]
)

# ---------------------------------------------------------------------------
# Intended track — branche 3ème
# ---------------------------------------------------------------------------

TRACK_3EME_IDS: frozenset[str] = frozenset(["general", "techno", "pro", "undecided"])

# ---------------------------------------------------------------------------
# Filières lycée
# ---------------------------------------------------------------------------

FILIERE_IDS: frozenset[str] = frozenset(["general", "techno", "pro"])

# ---------------------------------------------------------------------------
# Sous-filières techno
# ---------------------------------------------------------------------------

SOUS_FILIERE_IDS: frozenset[str] = frozenset(
    ["STMG", "STI2D", "ST2S", "STL", "STD2A", "STAV", "STHR"]
)

# ---------------------------------------------------------------------------
# Spécialités lycée général (13 entrées officielles ÉN 2026)
# ---------------------------------------------------------------------------

SPECIALITE_IDS: frozenset[str] = frozenset(
    [
        "mathematiques",
        "physique-chimie",
        "svt",
        "ses",
        "hggsp",
        "hlp",
        "llcer",
        "llca",
        "nsi",
        "arts",
        "si",
        "bio-ecologie",
        "eppcs",
    ]
)

# ---------------------------------------------------------------------------
# Spécialités bac pro (MVP)
# ---------------------------------------------------------------------------

SPECIALITE_PRO_IDS: frozenset[str] = frozenset(
    [
        "vente-action-commerciale",
        "accompagnement-soins-aide",
        "cuisine",
        "systemes-numeriques",
        "gestion-administration",
        "metiers-electricite",
        "maintenance-vehicules",
        "metiers-batiment-tp",
        "metiers-bois",
        "conduite-transport",
        "agro-alimentation-bio",
        "metiers-mode",
        "securite-prevention",
        "services-proximite",
        "metiers-production",
    ]
)

# ---------------------------------------------------------------------------
# Post-bac
# ---------------------------------------------------------------------------

POSTBAC_YEAR_IDS: frozenset[str] = frozenset(
    ["bac_year", "bac+1", "bac+2", "bac+3", "bac+4_plus", "pause"]
)

POSTBAC_FORMATION_IDS: frozenset[str] = frozenset(
    [
        "universite",
        "but",
        "bts",
        "cpge",
        "ecole_ingenieur",
        "ecole_commerce",
        "ecole_specialisee",
        "alternance",
        "aucune",
    ]
)

# ---------------------------------------------------------------------------
# Validation matrix — expected specialties count per (level, filiere)
# ---------------------------------------------------------------------------

def expected_spec_count(level: str, filiere: str | None) -> int | None:
    """Return expected number of lycée-général specialties, or None if N/A."""
    if filiere == "general":
        if level == "lycee_1ere":
            return 3
        if level == "lycee_terminale":
            return 2
    if filiere == "pro":
        if level in ("lycee_2nde", "lycee_1ere", "lycee_terminale"):
            return 1  # 1 bac pro spécialité
    return None


def requires_sous_filiere(level: str, filiere: str | None) -> bool:
    return filiere == "techno" and level in ("lycee_1ere", "lycee_terminale")
