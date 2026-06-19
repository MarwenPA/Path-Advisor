"""Profile maturity computation — Story 2.7 AC2.

Pure deterministic function: no DB calls, no side effects.
Shared logic: same algorithm in TypeScript at apps/web/src/lib/profile/maturity.ts.
Golden snapshot JSON validates both implementations stay aligned (AC9 anti-drift).

Principle: 3 qualitative states only — never a percentage.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol


class MaturityLevel(str, Enum):
    BASE = "base"
    ENRICHED = "enriched"
    COMPLETE = "complete"


# ---------------------------------------------------------------------------
# Snapshot protocol — duck-typed so callers can pass Django model instances
# or plain dataclasses without coupling to either.
# ---------------------------------------------------------------------------

class ProfileSnapshot(Protocol):
    onboarding_step1_status: str
    passions_count: int
    onboarding_step2_status: str
    bulletins_status: str


# Status constants — mirrors BulletinsStatus model enum (added by this story)
_BULLETINS_ENRICHED = {"partial"}
_BULLETINS_COMPLETE = {"completed"}


def _satisfies_complete(snap: ProfileSnapshot) -> bool:
    """Level 'complete' = strict completed on all 3 dimensions (AC2 table row 3)."""
    return (
        snap.onboarding_step1_status == "completed"
        and snap.onboarding_step2_status == "completed"
        and snap.bulletins_status in _BULLETINS_COMPLETE
    )


def compute_maturity(snap: ProfileSnapshot) -> MaturityLevel:
    """Return the qualitative maturity level for a profile snapshot.

    Evaluation order: complete → enriched → base.
    Every profile has at least 'base' as a valid state.
    """
    if _satisfies_complete(snap):
        return MaturityLevel.COMPLETE
    if snap.bulletins_status in _BULLETINS_ENRICHED or snap.bulletins_status in _BULLETINS_COMPLETE:
        # If bulletins are partial or completed but complete conditions not met → enriched
        return MaturityLevel.ENRICHED
    return MaturityLevel.BASE
