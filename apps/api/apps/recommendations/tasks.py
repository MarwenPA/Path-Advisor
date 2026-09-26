"""Story 9.5/9.6 — beat tasks: art. 22 journal retention (+ ML audit, 9.6)."""

from __future__ import annotations

import structlog
from celery import shared_task

log = structlog.get_logger(__name__)


@shared_task(name="recommendations.prune_scoring_decisions")
def prune_scoring_decisions_task(days: int = 365) -> int:
    """Story 9.5 — art. 22 journal retention (12 months, DPO note in the
    story doc). Personal data of minors must not accumulate forever."""
    from .model_governance import prune_scoring_decisions

    deleted = prune_scoring_decisions(days=days)
    log.info("recommendations.pruned_scoring_decisions", deleted=deleted, days=days)
    return deleted
