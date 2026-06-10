"""Dialog hash cross-check — Story 1.10 §T5.3.

Re-computes the SHA-256 of every canonical payload + asserts equality to
the stored hash. Any copy drift fails this test loudly, forcing the dev to
validate the new wording before shipping. See `dialog_hashes.py`.
"""

from __future__ import annotations

import pytest

from apps.profiles.access_list.dialog_hashes import (
    CANONICAL_REVOKE_DIALOG_HASHES,
    CANONICAL_REVOKE_DIALOG_PAYLOADS,
    compute_dialog_hash,
)


@pytest.mark.parametrize("tier", ["parent", "school", "counselor"])
def test_canonical_hash_matches_payload(tier):
    expected = CANONICAL_REVOKE_DIALOG_HASHES[tier]
    actual = compute_dialog_hash(CANONICAL_REVOKE_DIALOG_PAYLOADS[tier])
    assert expected == actual, (
        f"Tier {tier!r} hash drift — canonical hash != SHA-256(payload). "
        f"Either the payload changed without re-computing, or the hash was "
        f"hand-edited. Update both by re-running `compute_dialog_hash`."
    )


def test_every_tier_has_a_hash():
    """A new TierType in `dto.py` MUST have a payload here."""
    assert set(CANONICAL_REVOKE_DIALOG_HASHES.keys()) == {"parent", "school", "counselor"}


def test_payload_has_the_required_eight_fields():
    """Per spec : 8 fields. A typo (missing key) would silently change the hash."""
    required = {
        "version",
        "title",
        "subtitle",
        "consequence_main",
        "consequence_secondary",
        "confirmation_label",
        "primary_cta",
        "secondary_cta",
    }
    for tier, payload in CANONICAL_REVOKE_DIALOG_PAYLOADS.items():
        missing = required - set(payload.keys())
        assert not missing, f"Tier {tier!r} missing fields: {missing}"
