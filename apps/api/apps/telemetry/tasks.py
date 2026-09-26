"""Story 8.9 retention beat task (review fix P0-2).

`prune_rum_vitals` existed only as a management command that nothing
scheduled — while the public RGPD page promises the 90-day bound. The core
is shared with the command; the beat entry lives in `path_advisor/celery.py`.
No `with_system_actor`: `rum_vitals` carries no personal data and no RLS.
"""

from __future__ import annotations

from datetime import timedelta

import structlog
from celery import shared_task
from django.utils import timezone

from .models import RumVital
from .views import MAX_WINDOW_DAYS

log = structlog.get_logger(__name__)


def prune_rum_vitals(days: int = MAX_WINDOW_DAYS) -> int:
    cutoff = timezone.now() - timedelta(days=max(1, days))
    deleted, _ = RumVital.objects.filter(created_at__lt=cutoff).delete()
    return deleted


@shared_task(name="telemetry.prune_rum_vitals")
def prune_rum_vitals_task(days: int = MAX_WINDOW_DAYS) -> int:
    deleted = prune_rum_vitals(days=days)
    log.info("telemetry.pruned_rum_vitals", deleted=deleted, days=days)
    return deleted
