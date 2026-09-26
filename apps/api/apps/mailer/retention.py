"""Story 8.1 retention core — shared by the management command (ad-hoc ops)
and the beat task `mailer.prune_email_outbox` (review fix P0-2: the policy
only exists if something actually runs it)."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from .models import EmailOutbox, OutboxStatus


def prune_email_outbox(days: int = 90) -> int:
    """Delete terminal rows (sent/failed/skipped) older than `days`.

    QUEUED and SENDING are never pruned: they represent an email not yet
    delivered — `sweep_stale_outbox` is the tool that unsticks those.
    """
    cutoff = timezone.now() - timedelta(days=max(1, days))
    deleted, _ = (
        EmailOutbox.objects.filter(created_at__lt=cutoff)
        .exclude(status__in=[OutboxStatus.QUEUED, OutboxStatus.SENDING])
        .delete()
    )
    return deleted
