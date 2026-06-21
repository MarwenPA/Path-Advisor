"""Management command: seed_schools — idempotent seed for School + Parcours data.

Usage:
    uv run manage.py seed_schools

Story 4.3 — seeds School objects and 5+ Parcours covering multiple professions.
Safe to re-run: uses get_or_create / update_or_create throughout.

Requires professions to already be seeded (run after seed_professions or equivalent).
Professions not found in the DB are skipped with a warning.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.professions.models import Profession
from apps.schools.models import Parcours, School

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent / "fixtures" / "parcours_seed.json"


class Command(BaseCommand):
    help = "Seed School and Parcours data from parcours_seed.json (idempotent)."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Seeding schools and parcours…")
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        schools_created = 0
        schools_updated = 0
        parcours_created = 0
        parcours_updated = 0
        skipped = 0

        for entry in data:
            profession_slug = entry["profession_slug"]
            try:
                profession = Profession.objects.get(slug=profession_slug)
            except Profession.DoesNotExist:
                self.stderr.write(
                    f"  [SKIP] Profession slug '{profession_slug}' not found — seed professions first."
                )
                skipped += 1
                continue

            school_slug = entry["school_slug"]
            school, school_created = School.objects.update_or_create(
                slug=school_slug,
                defaults={
                    "name": entry["school_name"],
                    "city": entry.get("school_city", ""),
                    "school_type": entry.get("school_type", ""),
                    "is_active": True,
                },
            )
            if school_created:
                schools_created += 1
                self.stdout.write(f"  [CREATE] School: {school.name}")
            else:
                schools_updated += 1

            _, p_created = Parcours.objects.update_or_create(
                profession=profession,
                target_school=school,
                niveau_scolaire=entry.get("niveau_scolaire", ""),
                defaults={
                    "nodes": entry.get("nodes", []),
                    "edges": entry.get("edges", []),
                    "is_default": entry.get("is_default", False),
                },
            )
            if p_created:
                parcours_created += 1
                self.stdout.write(
                    f"  [CREATE] Parcours: {profession_slug} → {school_slug} "
                    f"({entry.get('niveau_scolaire', 'all')})"
                )
            else:
                parcours_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Schools: +{schools_created} updated {schools_updated}. "
                f"Parcours: +{parcours_created} updated {parcours_updated}. "
                f"Skipped: {skipped}."
            )
        )
