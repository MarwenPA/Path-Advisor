"""Golden-snapshot tests for compute_maturity() — Story 2.7 AC2 + AC9.

15 deterministic cases covering all 3 levels, edge-cases (skip, partial, new
user), and the client-server alignment check via the shared JSON golden file.

Run on SQLite (pure Python function — no DB calls needed).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest

from apps.students.profile_maturity import MaturityLevel, compute_maturity

# ---------------------------------------------------------------------------
# Fixture type ---------------------------------------------------------------
# ---------------------------------------------------------------------------

MaturityLevelStr = Literal["base", "enriched", "complete"]


@dataclass
class ProfileSnapshot:
    """Minimal snapshot fed to compute_maturity — mirrors AC2 table."""

    onboarding_step1_status: str
    passions_count: int
    onboarding_step2_status: str
    bulletins_status: str


# ---------------------------------------------------------------------------
# 15 golden cases -------------------------------------------------------------
# ---------------------------------------------------------------------------

GOLDEN_CASES: list[tuple[str, ProfileSnapshot, MaturityLevelStr]] = [
    # ── BASE ────────────────────────────────────────────────────────────────
    (
        "brand-new user (both steps pending, bulletins pending)",
        ProfileSnapshot(
            onboarding_step1_status="pending",
            passions_count=0,
            onboarding_step2_status="pending",
            bulletins_status="pending",
        ),
        "base",
    ),
    (
        "step1 skipped + step2 skipped + bulletins pending",
        ProfileSnapshot(
            onboarding_step1_status="skipped",
            passions_count=0,
            onboarding_step2_status="skipped",
            bulletins_status="pending",
        ),
        "base",
    ),
    (
        "step1 completed + step2 skipped + bulletins postponed",
        ProfileSnapshot(
            onboarding_step1_status="completed",
            passions_count=5,
            onboarding_step2_status="skipped",
            bulletins_status="postponed",
        ),
        "base",
    ),
    (
        "step1 partial_skipped (≥3 passions) + step2 completed + bulletins pending",
        ProfileSnapshot(
            onboarding_step1_status="partial_skipped",
            passions_count=3,
            onboarding_step2_status="completed",
            bulletins_status="pending",
        ),
        "base",
    ),
    (
        "step1 in_progress (no passions) + step2 pending + bulletins pending",
        ProfileSnapshot(
            onboarding_step1_status="in_progress",
            passions_count=0,
            onboarding_step2_status="pending",
            bulletins_status="pending",
        ),
        "base",
    ),
    (
        "step1 completed + step2 completed + bulletins postponed",
        ProfileSnapshot(
            onboarding_step1_status="completed",
            passions_count=6,
            onboarding_step2_status="completed",
            bulletins_status="postponed",
        ),
        "base",
    ),
    # ── ENRICHED ─────────────────────────────────────────────────────────────
    (
        "step1 completed + step2 completed + bulletins partial",
        ProfileSnapshot(
            onboarding_step1_status="completed",
            passions_count=5,
            onboarding_step2_status="completed",
            bulletins_status="partial",
        ),
        "enriched",
    ),
    (
        "step1 skipped + step2 skipped + bulletins partial (min config enriched)",
        ProfileSnapshot(
            onboarding_step1_status="skipped",
            passions_count=0,
            onboarding_step2_status="skipped",
            bulletins_status="partial",
        ),
        "enriched",
    ),
    (
        "step1 partial_skipped (≥3 passions) + step2 skipped + bulletins partial",
        ProfileSnapshot(
            onboarding_step1_status="partial_skipped",
            passions_count=4,
            onboarding_step2_status="skipped",
            bulletins_status="partial",
        ),
        "enriched",
    ),
    (
        "step1 in_progress (2 passions <3) + step2 pending + bulletins partial — still enriched",
        ProfileSnapshot(
            onboarding_step1_status="in_progress",
            passions_count=2,
            onboarding_step2_status="pending",
            bulletins_status="partial",
        ),
        "enriched",
    ),
    # ── COMPLETE ──────────────────────────────────────────────────────────────
    (
        "step1 completed + step2 completed + bulletins completed",
        ProfileSnapshot(
            onboarding_step1_status="completed",
            passions_count=5,
            onboarding_step2_status="completed",
            bulletins_status="completed",
        ),
        "complete",
    ),
    (
        "step1 completed (8 passions) + step2 completed + bulletins completed",
        ProfileSnapshot(
            onboarding_step1_status="completed",
            passions_count=8,
            onboarding_step2_status="completed",
            bulletins_status="completed",
        ),
        "complete",
    ),
    # ── EDGE CASES ────────────────────────────────────────────────────────────
    (
        "step1 skipped + step2 completed + bulletins completed — NOT complete (step1 must be completed)",
        ProfileSnapshot(
            onboarding_step1_status="skipped",
            passions_count=0,
            onboarding_step2_status="completed",
            bulletins_status="completed",
        ),
        "enriched",
    ),
    (
        "step1 completed + step2 skipped + bulletins completed — NOT complete (step2 must be completed)",
        ProfileSnapshot(
            onboarding_step1_status="completed",
            passions_count=5,
            onboarding_step2_status="skipped",
            bulletins_status="completed",
        ),
        "enriched",
    ),
    (
        "partial_skipped step1 with <3 passions + step2 pending + bulletins completed — enriched (not base, not complete)",
        ProfileSnapshot(
            onboarding_step1_status="partial_skipped",
            passions_count=1,
            onboarding_step2_status="pending",
            bulletins_status="completed",
        ),
        "enriched",
    ),
]


@pytest.mark.parametrize("label,snapshot,expected", GOLDEN_CASES, ids=[c[0] for c in GOLDEN_CASES])
def test_compute_maturity_golden(label: str, snapshot: ProfileSnapshot, expected: MaturityLevelStr) -> None:
    result = compute_maturity(snapshot)
    assert result == MaturityLevel(expected), (
        f"Case: {label!r}\n"
        f"  snapshot={snapshot}\n"
        f"  expected={expected!r}, got={result.value!r}"
    )


# ---------------------------------------------------------------------------
# Client–server alignment test -----------------------------------------------
# ---------------------------------------------------------------------------

GOLDEN_JSON_PATH = (
    Path(__file__).parent.parent.parent.parent.parent.parent  # repo root
    / "apps/web/src/lib/profile/golden-maturity.test.json"
)


def test_golden_json_aligns_with_backend() -> None:
    """AC2 — same golden JSON must yield the same result in Python and TS.

    The JSON is authoritative. If this test fails, either:
    - The JSON needs to be updated to reflect spec changes, OR
    - The Python implementation has drifted from the spec.
    """
    if not GOLDEN_JSON_PATH.exists():
        pytest.skip(f"Golden JSON not yet generated: {GOLDEN_JSON_PATH}")

    cases = json.loads(GOLDEN_JSON_PATH.read_text())
    for case in cases:
        snapshot = ProfileSnapshot(
            onboarding_step1_status=case["onboarding_step1_status"],
            passions_count=case["passions_count"],
            onboarding_step2_status=case["onboarding_step2_status"],
            bulletins_status=case["bulletins_status"],
        )
        expected = MaturityLevel(case["expected"])
        result = compute_maturity(snapshot)
        assert result == expected, (
            f"Golden drift in case {case['id']!r}: "
            f"expected {expected.value!r}, got {result.value!r}"
        )
