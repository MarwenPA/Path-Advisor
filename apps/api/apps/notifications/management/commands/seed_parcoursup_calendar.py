"""Story 8.3 — idempotent seed of the current campaign's milestones.

"Configuration admin" for the MVP: dates are public and known in advance;
re-running updates dates in place (get_or_create by kind+campaign, then
update). A visual CRUD belongs to Epic 9.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from django.core.management.base import BaseCommand

from apps.notifications.models import MilestoneKind, ParcoursupMilestone

CAMPAIGN = "2026-2027"

#: (kind, date, notify_days_before) — official 2026-2027 calendar shape.
MILESTONES: list[tuple[str, date, int]] = [
    (MilestoneKind.OUVERTURE, date(2027, 1, 20), 18),
    (MilestoneKind.J30_FERMETURE_VOEUX, date(2027, 3, 11), 30),
    (MilestoneKind.FERMETURE_VOEUX, date(2027, 3, 11), 7),
    (MilestoneKind.RESULTATS_PRINCIPALE, date(2027, 6, 2), 5),
    (MilestoneKind.RESULTATS_COMPLEMENTAIRE, date(2027, 6, 15), 3),
]


class Command(BaseCommand):
    help = "Seed/update the Parcoursup milestone calendar for the current campaign."

    def handle(self, *args: Any, **options: Any) -> None:
        created = updated = 0
        for kind, when, days_before in MILESTONES:
            obj, was_created = ParcoursupMilestone.objects.get_or_create(
                kind=kind,
                campaign=CAMPAIGN,
                defaults={"date": when, "notify_days_before": days_before},
            )
            if was_created:
                created += 1
            elif (obj.date, obj.notify_days_before) != (when, days_before):
                obj.date, obj.notify_days_before = when, days_before
                obj.save(update_fields=["date", "notify_days_before"])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Milestones: {created} created, {updated} updated."))
