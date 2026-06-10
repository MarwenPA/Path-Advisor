"""Visibility-matrix integrity — Story 1.9 §T2.3.

These tests guard the SoT promise of ``visibility_matrix.py`` : every tier
has both ``visible`` and ``masked`` keys, those keys partition
``KNOWN_DATA_AREAS`` exactly (no overlap, no leftover), and only canonical
area names appear.
"""

from __future__ import annotations

import pytest

from apps.profiles.access_list.dto import TierType
from apps.profiles.access_list.visibility_matrix import (
    KNOWN_DATA_AREAS,
    VISIBILITY_MATRIX,
)

# We list the expected tier types explicitly so a typo in `VISIBILITY_MATRIX`
# is caught — not silently absorbed by iterating the dict.
_EXPECTED_TIERS: tuple[TierType, ...] = ("parent", "school", "counselor")


def test_every_expected_tier_present():
    assert set(VISIBILITY_MATRIX.keys()) == set(_EXPECTED_TIERS)


@pytest.mark.parametrize("tier", _EXPECTED_TIERS)
def test_tier_has_visible_and_masked_keys(tier):
    entry = VISIBILITY_MATRIX[tier]
    assert "visible" in entry and "masked" in entry, (
        f"VISIBILITY_MATRIX[{tier!r}] missing visible/masked keys"
    )


@pytest.mark.parametrize("tier", _EXPECTED_TIERS)
def test_tier_visible_masked_partition_known_areas(tier):
    """Visible + masked MUST equal KNOWN_DATA_AREAS, with no overlap."""
    visible = set(VISIBILITY_MATRIX[tier]["visible"])
    masked = set(VISIBILITY_MATRIX[tier]["masked"])

    overlap = visible & masked
    assert not overlap, f"Tier {tier!r} has visible/masked overlap: {overlap}"

    union = visible | masked
    missing = KNOWN_DATA_AREAS - union
    extras = union - KNOWN_DATA_AREAS
    assert not missing, f"Tier {tier!r} missing data areas: {missing}"
    assert not extras, f"Tier {tier!r} references unknown data areas: {extras}"
