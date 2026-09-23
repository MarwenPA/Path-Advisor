"""Story 8.9 — retention for anonymous RUM rows (data minimisation).

The rows carry no personal data by construction, but GDPR minimisation still
wants telemetry bounded in time — and the p75 summary only ever reads a
90-day window (`MAX_WINDOW_DAYS`), so anything older is dead weight anyway.
Intended to run from cron/Celery beat; safe to run ad hoc (idempotent).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.telemetry.models import RumVital
from apps.telemetry.views import MAX_WINDOW_DAYS


class Command(BaseCommand):
    help = "Delete RUM vitals older than --days (default: 90, the summary's max window)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--days", type=int, default=MAX_WINDOW_DAYS)

    def handle(self, *args: Any, **options: Any) -> None:
        days = max(1, options["days"])
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = RumVital.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Pruned {deleted} RUM rows older than {days} days."))
