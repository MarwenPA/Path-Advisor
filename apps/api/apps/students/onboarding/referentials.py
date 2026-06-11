"""Onboarding step-1 referentials — Python mirror of the frontend source.

The TypeScript source of truth is at
`apps/web/src/lib/onboarding/referentials.ts`. The `test_referentials_sync`
pytest enforces that both sides ship the same PASSION_IDS and VALEUR_IDS so
drift between front and back is caught at CI time.

These constants are imported by the onboarding serializers (Story 2.1 T3) to
validate PATCH payloads against the curated referential. Labels and aliases
are duplicated for symmetry but the backend only consumes the ID sets.
"""

from __future__ import annotations

import re
from typing import Final

# --- Passions ---------------------------------------------------------------

PASSION_IDS: Final[tuple[str, ...]] = (
    "sciences-nature",
    "tech-code",
    "arts-creation",
    "sport-corps",
    "aider-autres",
    "musique",
    "cinema-series",
    "lecture-ecriture",
    "voyage-cultures",
    "cuisine",
    "mode-style",
    "business-argent",
    "jeux-video",
    "animaux",
    "education-transmission",
    "sante-soin",
    "politique-societe",
    "bricolage-mains",
    "communication-media",
    "spiritualite-sens",
)

# --- Valeurs ----------------------------------------------------------------

VALEUR_IDS: Final[tuple[str, ...]] = (
    "justice-sociale",
    "independance",
    "securite",
    "creativite",
    "defi",
    "contact-humain",
    "reconnaissance",
    "argent-confort",
    "apprendre",
    "nature-vivant",
    "aventure",
    "sens-utilite",
)

# --- Limits (mirror) --------------------------------------------------------

CUSTOM_PASSION_PREFIX: Final[str] = "custom:"
MAX_CUSTOM_PASSIONS: Final[int] = 5
MAX_PASSIONS_TOTAL: Final[int] = 8
MIN_PASSIONS: Final[int] = 3
MIN_VALEURS: Final[int] = 3
MAX_VALEURS: Final[int] = 5
MAX_INTERET_CHARS: Final[int] = 200

# Slug accepted after the `custom:` prefix. Same regex as the frontend
# `customSlugRegex`: 1-30 chars, lowercase ASCII letters/digits/hyphens, no
# leading/trailing hyphen.
_CUSTOM_SLUG_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,28}[a-z0-9])?$"
)

# --- Sets for O(1) lookup ---------------------------------------------------

PASSION_ID_SET: Final[frozenset[str]] = frozenset(PASSION_IDS)
VALEUR_ID_SET: Final[frozenset[str]] = frozenset(VALEUR_IDS)


def is_valid_passion_id(value: str) -> bool:
    """A passion ID is valid if it's in the referential OR a well-formed custom:<slug>."""
    if not isinstance(value, str) or not value:
        return False
    if value in PASSION_ID_SET:
        return True
    if not value.startswith(CUSTOM_PASSION_PREFIX):
        return False
    slug = value[len(CUSTOM_PASSION_PREFIX) :]
    return bool(_CUSTOM_SLUG_RE.match(slug))


def is_valid_valeur_id(value: str) -> bool:
    return isinstance(value, str) and value in VALEUR_ID_SET


def validate_passions_array(values: list[str]) -> tuple[bool, str | None]:
    """Validate a passions list. Returns (is_valid, error_msg)."""
    if len(values) > MAX_PASSIONS_TOTAL:
        return False, f"Maximum {MAX_PASSIONS_TOTAL} passions total."
    if len(values) != len(set(values)):
        return False, "Passion IDs must be unique."
    custom_count = sum(1 for v in values if v.startswith(CUSTOM_PASSION_PREFIX))
    if custom_count > MAX_CUSTOM_PASSIONS:
        return False, f"Maximum {MAX_CUSTOM_PASSIONS} custom passions."
    for v in values:
        if not is_valid_passion_id(v):
            return False, f"Unknown passion ID: {v!r}."
    return True, None


def validate_valeurs_array(values: list[str]) -> tuple[bool, str | None]:
    if len(values) > MAX_VALEURS:
        return False, f"Maximum {MAX_VALEURS} valeurs."
    if len(values) != len(set(values)):
        return False, "Valeur IDs must be unique."
    for v in values:
        if not is_valid_valeur_id(v):
            return False, f"Unknown valeur ID: {v!r}."
    return True, None


def validate_interets_record(record: dict[str, str | None]) -> tuple[bool, str | None]:
    expected_keys = {"1", "2", "3"}
    if set(record.keys()) != expected_keys:
        return False, "Intérêts record must have keys '1', '2', '3'."
    for k, v in record.items():
        if v is None:
            continue
        if not isinstance(v, str):
            return False, f"Intérêt {k} must be a string or null."
        if len(v) > MAX_INTERET_CHARS:
            return False, f"Intérêt {k} exceeds {MAX_INTERET_CHARS} chars."
    return True, None
