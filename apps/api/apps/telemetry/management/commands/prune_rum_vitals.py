"""Story 8.9 — retention for anonymous RUM rows (data minimisation).

The rows carry no personal data by construction, but GDPR minimisation still
wants telemetry bounded in time — and the p75 summary only ever reads a
90-day window (`MAX_WINDOW_DAYS`), so anything older is dead weight anyway.
Runs daily via the beat task `telemetry.prune_rum_vitals` (review fix P0-2);
this command is the ad-hoc ops entry point.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.telemetry.tasks import prune_rum_vitals
from apps.telemetry.views import MAX_WINDOW_DAYS


class Command(BaseCommand):
    help = "Delete RUM vitals older than --days (default: 90, the summary's max window)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--days", type=int, default=MAX_WINDOW_DAYS)

    def handle(self, *args: Any, **options: Any) -> None:
        days = max(1, options["days"])
        deleted = prune_rum_vitals(days=days)
        self.stdout.write(self.style.SUCCESS(f"Pruned {deleted} RUM rows older than {days} days."))
