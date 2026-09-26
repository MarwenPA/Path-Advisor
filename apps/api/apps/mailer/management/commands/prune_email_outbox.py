"""Story 8.1 — retention for outbox rows (data minimisation, same rationale
as `prune_rum_vitals`): recipient addresses and token-bearing contexts must
not accumulate forever on an app serving minors.

The core lives in `mailer.retention` and runs daily via the beat task
`mailer.prune_email_outbox` (review fix P0-2); this command is the ad-hoc
ops entry point with a custom --days.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.mailer.retention import prune_email_outbox


class Command(BaseCommand):
    help = (
        "Delete terminal outbox rows (sent/failed/skipped) older than --days "
        "(default 90). Queued/sending rows are kept."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--days", type=int, default=90)

    def handle(self, *args: Any, **options: Any) -> None:
        deleted = prune_email_outbox(days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"Pruned {deleted} outbox row(s)."))
