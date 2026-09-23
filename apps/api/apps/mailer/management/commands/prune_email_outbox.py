"""Story 8.1 — retention for outbox rows (data minimisation, same rationale
as `prune_rum_vitals`): recipient addresses and token-bearing contexts must
not accumulate forever on an app serving minors."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.mailer.models import EmailOutbox, OutboxStatus


class Command(BaseCommand):
    help = "Delete sent/failed outbox rows older than --days (default 90). Queued rows are kept."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--days", type=int, default=90)

    def handle(self, *args: Any, **options: Any) -> None:
        cutoff = timezone.now() - timedelta(days=max(1, options["days"]))
        deleted, _ = (
            EmailOutbox.objects.filter(created_at__lt=cutoff)
            .exclude(status=OutboxStatus.QUEUED)
            .delete()
        )
        self.stdout.write(self.style.SUCCESS(f"Pruned {deleted} outbox row(s)."))
