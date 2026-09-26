"""Story 8.1 — replay terminally-failed outbox rows (AC3's "replayable" half).

Run after the failure cause is fixed (SMTP back up, template restored).
Resets `failed` rows to `queued` with a fresh attempt budget and re-enqueues
delivery. Idempotent; bounded by --limit to avoid thundering-herd replays.

Concurrent-safe (review fix P3): the re-queue is a CONDITIONAL update —
two operators running this at once cannot both claim the same row, and
`deliver_email`'s own CAS makes a stray duplicate task a no-op anyway. If
the `.delay()` fails after the flip, the row is a fresh QUEUED orphan and
`sweep_stale_outbox` re-enqueues it within 15 minutes.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.mailer.models import EmailOutbox, OutboxStatus
from apps.mailer.tasks import deliver_email


class Command(BaseCommand):
    help = "Re-queue failed outbox emails (use after fixing the failure cause)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args: Any, **options: Any) -> None:
        pks = list(
            EmailOutbox.objects.filter(status=OutboxStatus.FAILED)
            .order_by("created_at")
            .values_list("pk", flat=True)[: max(1, options["limit"])]
        )
        requeued = 0
        for pk in pks:
            claimed = EmailOutbox.objects.filter(pk=pk, status=OutboxStatus.FAILED).update(
                status=OutboxStatus.QUEUED,
                attempts=0,
                last_error="",
                updated_at=timezone.now(),
            )
            if claimed:
                deliver_email.delay(pk)
                requeued += 1
        self.stdout.write(self.style.SUCCESS(f"Re-queued {requeued} failed email(s)."))
