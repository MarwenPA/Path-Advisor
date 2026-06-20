"""Story 2.6 T2 — Celery worker stub for async profile recompute.

Epic 3 (Recommandation vocationnelle) will wire the real implementation.
This stub satisfies the contract: idempotent, logs trigger_reason, updates
`recomputed_at` once Epic 3 lands.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def recompute_for_student(student_id: str, trigger_reason: str = "manual") -> None:
    """Enqueue or execute a profile recompute for the given student.

    Args:
        student_id: Primary key of `StudentProfile`.
        trigger_reason: One of "profile_major_change", "bulletin_added",
            "bulletin_deleted", "passions_updated", "level_updated", "manual".
    """
    logger.info(
        "recompute_for_student queued",
        extra={"student_id": student_id, "trigger_reason": trigger_reason},
    )
    # Epic 3 TODO: call actual scoring pipeline here.
    # When Celery is configured, decorate this function with @shared_task
    # and call recompute_for_student.apply_async(args=[student_id, trigger_reason],
    #     countdown=5, expires=300).
