"""Story 8.1 — replay terminally-failed outbox rows (AC3's "replayable" half).

Run after the failure cause is fixed (SMTP back up, template restored).
Resets `failed` rows to `queued` with a fresh attempt budget and re-enqueues
delivery. Idempotent; bounded by --limit to avoid thundering-herd replays.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.mailer.models import EmailOutbox, OutboxStatus
from apps.mailer.tasks import deliver_email


class Command(BaseCommand):
    help = "Re-queue failed outbox emails (use after fixing the failure cause)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args: Any, **options: Any) -> None:
        rows = list(
            EmailOutbox.objects.filter(status=OutboxStatus.FAILED).order_by("created_at")[
                : max(1, options["limit"])
            ]
        )
        for row in rows:
            row.status = OutboxStatus.QUEUED
            row.attempts = 0
            row.save(update_fields=["status", "attempts"])
            deliver_email.delay(row.pk)
        self.stdout.write(self.style.SUCCESS(f"Re-queued {len(rows)} failed email(s)."))
