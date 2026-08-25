"""Management command : load the 50+ curated professions — Story 3.2 T2."""

from __future__ import annotations

import copy

from django.core.management.base import BaseCommand

from apps.professions.management.commands._seed_data_part1 import PROFESSIONS_PART1
from apps.professions.management.commands._seed_data_part2 import PROFESSIONS_PART2
from apps.professions.management.commands._seed_data_part3 import PROFESSIONS_PART3
from apps.professions.management.commands._seed_extensions import (
    DESCRIPTION_EXTENSIONS,
    ROUTINE_EXTENSIONS,
)
from apps.professions.models import Profession

_RAW_PROFESSIONS = PROFESSIONS_PART1 + PROFESSIONS_PART2 + PROFESSIONS_PART3


def _apply_extensions(raw: list[dict]) -> list[dict]:
    """Apply AC3 extension snippets to entries whose word counts are below minimums."""
    result = []
    for item in raw:
        data = copy.deepcopy(item)
        slug = data["slug"]
        if slug in DESCRIPTION_EXTENSIONS:
            data["description"] = data["description"].rstrip() + DESCRIPTION_EXTENSIONS[slug]
        if slug in ROUTINE_EXTENSIONS:
            data["daily_routine"] = data["daily_routine"].rstrip() + ROUTINE_EXTENSIONS[slug]
        result.append(data)
    return result


ALL_PROFESSIONS = _apply_extensions(_RAW_PROFESSIONS)


class Command(BaseCommand):
    help = "Seed the professions referential with 50+ curated MVP occupations (Story 3.2)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing professions before seeding (use with caution).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Profession.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing professions."))

        created = 0
        updated = 0

        for data in ALL_PROFESSIONS:
            slug = data["slug"]
            _obj, is_new = Profession.objects.update_or_create(
                slug=slug,
                defaults={k: v for k, v in data.items() if k != "slug"},
            )
            if is_new:
                created += 1
            else:
                updated += 1

        total = Profession.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Professions seed complete: {created} created, {updated} updated. "
                f"Total active: {total}."
            )
        )
