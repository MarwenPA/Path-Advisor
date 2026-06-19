"""Fuzzy mapping from OCR-extracted subject names to canonical referential IDs.

Uses Levenshtein edit distance (threshold < 3) to map OCR noise to known
subject keys. Falls back to `unmapped: True` if no match found — the student
can correct manually in the recap (AC5).

Example:
    "Math" / "Mathematiques" / "MATH" → "mathematiques"
    "Truc Inconnu" → unmapped=True (kept as-is for student review)
"""

from __future__ import annotations

import unicodedata

try:
    from Levenshtein import distance as levenshtein_distance
    _LEVENSHTEIN_AVAILABLE = True
except ImportError:
    _LEVENSHTEIN_AVAILABLE = False


def _normalize(text: str) -> str:
    """Lowercase + remove accents + strip punctuation for fuzzy comparison."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(c for c in ascii_str if c.isalnum() or c == " ").strip()


# Canonical subject referential — keyed by normalized name.
# This is intentionally flat; the real versioned referential lives in
# `packages/copy/onboarding/subjects-by-level.ts` (front-end) and will be
# migrated to a DB table in Story 9.1.
CANONICAL_SUBJECTS: dict[str, str] = {
    "mathematiques": "mathematiques",
    "maths": "mathematiques",
    "math": "mathematiques",
    "francais": "francais",
    "lettres": "francais",
    "histoire geographie": "histoire_geo",
    "histoire geo": "histoire_geo",
    "histgeo": "histoire_geo",
    "hggsp": "hggsp",
    "physique chimie": "physique_chimie",
    "pc": "physique_chimie",
    "sciences vie terre": "svt",
    "svt": "svt",
    "biologie": "svt",
    "anglais": "anglais",
    "lv1 anglais": "anglais",
    "espagnol": "espagnol",
    "lv2 espagnol": "espagnol",
    "allemand": "allemand",
    "philosophie": "philosophie",
    "philo": "philosophie",
    "education physique sportive": "eps",
    "eps": "eps",
    "sport": "eps",
    "sciences economiques sociales": "ses",
    "ses": "ses",
    "nsi": "nsi",
    "numerique sciences informatique": "nsi",
    "humanites litterature philosophie": "hlp",
    "hlp": "hlp",
    "arts plastiques": "arts_plastiques",
    "musique": "musique",
    "technologie": "technologie",
    "techno": "technologie",
    "emc": "emc",
    "enseignement moral civique": "emc",
}

LEVENSHTEIN_THRESHOLD = 3


def map_subject(raw_name: str) -> dict:
    """Map an OCR-extracted subject name to its canonical ID.

    Returns:
        {"canonical_id": "mathematiques", "unmapped": False, "raw": "Maths"} on match
        {"canonical_id": None, "unmapped": True, "raw": "Truc Inconnu"} on miss
    """
    if not raw_name or not raw_name.strip():
        return {"canonical_id": None, "unmapped": True, "raw": raw_name}

    normalized = _normalize(raw_name)

    if len(normalized) > 100:
        return {"canonical_id": None, "unmapped": True, "raw": raw_name}

    # Exact match first
    if normalized in CANONICAL_SUBJECTS:
        return {"canonical_id": CANONICAL_SUBJECTS[normalized], "unmapped": False, "raw": raw_name}

    # Levenshtein fuzzy match
    if _LEVENSHTEIN_AVAILABLE:
        best_match: str | None = None
        best_dist = LEVENSHTEIN_THRESHOLD  # exclusive upper bound

        for candidate in CANONICAL_SUBJECTS:
            dist = levenshtein_distance(normalized, candidate)
            if dist < best_dist:
                best_dist = dist
                best_match = candidate

        if best_match:
            return {
                "canonical_id": CANONICAL_SUBJECTS[best_match],
                "unmapped": False,
                "raw": raw_name,
            }

    # No match — keep raw, flag unmapped
    return {"canonical_id": None, "unmapped": True, "raw": raw_name}
