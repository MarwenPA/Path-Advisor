"""Management command: seed_schools — idempotent seed for School + Parcours data.

Usage:
    uv run manage.py seed_schools

Story 4.3 — seeds School objects and 5+ Parcours covering multiple professions from
the parcours_seed.json fixture file.
Story 4.7 — also seeds Parcours entries with NiveauScolaire enum values (4+ bac pro,
2+ terminale_generale) via PARCOURS_SEED Python list.

Safe to re-run: uses get_or_create / update_or_create throughout.

Requires professions to already be seeded (run after seed_professions or equivalent).
Professions not found in the DB are skipped with a warning.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.professions.models import Profession
from apps.schools.models import Parcours, School

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent / "fixtures" / "parcours_seed.json"


# ---------------------------------------------------------------------------
# Parcours seed data — Story 4.7
# ---------------------------------------------------------------------------

# Bac Pro parcours (troisieme_bac_pro) — AC6 requires >= 4
PARCOURS_SEED = [
    # 1. Technicien aéronautique — troisieme_bac_pro
    {
        "profession_slug": "technicien-aeronautique",
        "profession_defaults": {
            "name": "Technicien aéronautique",
            "description": (
                "Le technicien aéronautique assure la maintenance et la réparation "
                "des aéronefs et de leurs équipements."
            ),
            "daily_routine": (
                "Tu commences ta matinée en inspectant les systèmes avioniques de "
                "l'aéronef, puis tu procèdes aux vérifications réglementaires."
            ),
            "requirements_json": [{"type": "skill", "label": "Mécanique aéronautique"}],
            "prospects_text": "Technicien avionique, Ingénieur maintenance aéronautique.",
            "signals_json": {
                "passions": ["aviation", "mécanique"],
                "keywords": ["aéronautique", "avion", "maintenance"],
            },
            "level_compatibility": ["lycee_1ere_tle_pro", "college_3eme"],
        },
        "target_school_slug": "lycee-pro-saint-exupery-marseille",
        "niveau_scolaire": Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        "is_default": True,
        "label": "Voie bac pro aéronautique depuis la 3ème",
        "nodes": [
            {"id": "start", "label": "3ème", "type": "start"},
            {
                "id": "node1",
                "label": "Bac Pro Aéronautique option Avionique",
                "type": "diplome",
                "schoolSlug": "lycee-pro-saint-exupery-marseille",
            },
            {"id": "node2", "label": "BTS Aéronautique", "type": "diplome"},
            {
                "id": "target",
                "label": "Poursuite école d'ingé en alternance",
                "type": "target",
                "schoolSlug": None,
            },
        ],
        "edges": [
            {"source": "start", "target": "node1"},
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "target"},
        ],
    },
    # 2. Cuisinier — troisieme_bac_pro
    {
        "profession_slug": "cuisinier",
        "profession_defaults": {
            "name": "Cuisinier",
            "description": (
                "Le cuisinier prépare et réalise des mets variés pour les clients "
                "d'un restaurant ou d'une collectivité."
            ),
            "daily_routine": (
                "Tu commences ta matinée en préparant les ingrédients du service du "
                "midi, puis tu élabores les plats selon les recettes du chef."
            ),
            "requirements_json": [{"type": "skill", "label": "Techniques culinaires"}],
            "prospects_text": "Chef de partie, Sous-chef, Chef de cuisine.",
            "signals_json": {
                "passions": ["cuisine", "gastronomie"],
                "keywords": ["cuisine", "restauration", "gastronomie"],
            },
            "level_compatibility": ["lycee_1ere_tle_pro", "college_3eme"],
        },
        "target_school_slug": "lycee-pro-nicolas-appert-orvault",
        "niveau_scolaire": Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        "is_default": True,
        "label": "Voie bac pro cuisine depuis la 3ème",
        "nodes": [
            {"id": "start", "label": "3ème", "type": "start"},
            {
                "id": "node1",
                "label": "CAP Cuisine",
                "type": "diplome",
                "schoolSlug": "lycee-pro-nicolas-appert-orvault",
            },
            {
                "id": "node2",
                "label": "Bac Pro Cuisine",
                "type": "diplome",
                "schoolSlug": "lycee-pro-nicolas-appert-orvault",
            },
            {
                "id": "target",
                "label": "Chef de cuisine",
                "type": "target",
                "schoolSlug": None,
            },
        ],
        "edges": [
            {"source": "start", "target": "node1"},
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "target"},
        ],
    },
    # 3. Électricien — troisieme_bac_pro
    {
        "profession_slug": "electricien",
        "profession_defaults": {
            "name": "Électricien",
            "description": (
                "L'électricien installe, entretient et répare les installations "
                "électriques dans les bâtiments et les industries."
            ),
            "daily_routine": (
                "Tu commences ta matinée en lisant les plans électriques du chantier, "
                "puis tu poses les câbles et raccordes les armoires électriques."
            ),
            "requirements_json": [{"type": "skill", "label": "Électrotechnique"}],
            "prospects_text": "Chef d'équipe électricité, Technicien de maintenance, Conducteur de travaux.",
            "signals_json": {
                "passions": ["électricité", "technique"],
                "keywords": ["électricien", "bâtiment", "énergie"],
            },
            "level_compatibility": ["lycee_1ere_tle_pro", "college_3eme"],
        },
        "target_school_slug": "lycee-pro-leonard-de-vinci-melun",
        "niveau_scolaire": Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        "is_default": True,
        "label": "Voie bac pro électrotechnique depuis la 3ème",
        "nodes": [
            {"id": "start", "label": "3ème", "type": "start"},
            {
                "id": "node1",
                "label": "Bac Pro Électrotechnique",
                "type": "diplome",
                "schoolSlug": "lycee-pro-leonard-de-vinci-melun",
            },
            {"id": "node2", "label": "BTS Électrotechnique", "type": "diplome"},
            {
                "id": "target",
                "label": "Technicien électricien senior",
                "type": "target",
                "schoolSlug": None,
            },
        ],
        "edges": [
            {"source": "start", "target": "node1"},
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "target"},
        ],
    },
    # 4. Mécanicien auto — troisieme_bac_pro
    {
        "profession_slug": "mecanicien-auto",
        "profession_defaults": {
            "name": "Mécanicien automobile",
            "description": (
                "Le mécanicien automobile assure la maintenance, le diagnostic "
                "et la réparation des véhicules."
            ),
            "daily_routine": (
                "Tu commences ta matinée en accueillant les véhicules en atelier, "
                "puis tu réalises les diagnostics via les outils informatiques."
            ),
            "requirements_json": [{"type": "skill", "label": "Mécanique automobile"}],
            "prospects_text": "Chef d'atelier, Expert technique, Diagnosticien.",
            "signals_json": {
                "passions": ["automobile", "mécanique"],
                "keywords": ["mécanique", "automobile", "moteur"],
            },
            "level_compatibility": ["lycee_1ere_tle_pro", "college_3eme"],
        },
        "target_school_slug": "lycee-pro-saint-exupery-marseille",
        "niveau_scolaire": Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        "is_default": True,
        "label": "Voie bac pro maintenance auto depuis la 3ème",
        "nodes": [
            {"id": "start", "label": "3ème", "type": "start"},
            {
                "id": "node1",
                "label": "Bac Pro Maintenance Auto",
                "type": "diplome",
                "schoolSlug": "lycee-pro-saint-exupery-marseille",
            },
            {"id": "node2", "label": "BTS MAVA", "type": "diplome"},
            {
                "id": "target",
                "label": "Chef d'atelier automobile",
                "type": "target",
                "schoolSlug": None,
            },
        ],
        "edges": [
            {"source": "start", "target": "node1"},
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "target"},
        ],
    },
    # 5. Technicien aéronautique — terminale_generale
    {
        "profession_slug": "technicien-aeronautique",
        "target_school_slug": "insa-lyon",
        "niveau_scolaire": Parcours.NiveauScolaire.TERMINALE_GENERALE,
        "is_default": False,
        "label": "Voie terminale générale → INSA",
        "nodes": [
            {"id": "start", "label": "Terminale Générale (Maths/PC)", "type": "start"},
            {"id": "node1", "label": "CPGE PTSI", "type": "diplome"},
            {
                "id": "target",
                "label": "INSA Lyon — Génie Mécanique",
                "type": "target",
                "schoolSlug": "insa-lyon",
            },
        ],
        "edges": [
            {"source": "start", "target": "node1"},
            {"source": "node1", "target": "target"},
        ],
    },
    # 6. Cuisinier — terminale_generale
    {
        "profession_slug": "cuisinier",
        "target_school_slug": None,
        "niveau_scolaire": Parcours.NiveauScolaire.TERMINALE_GENERALE,
        "is_default": False,
        "label": "Voie terminale générale vers la restauration gastronomique",
        "nodes": [
            {"id": "start", "label": "Terminale Générale", "type": "start"},
            {"id": "node1", "label": "BTS Hôtellerie-Restauration", "type": "diplome"},
            {
                "id": "target",
                "label": "Chef de cuisine gastronomique",
                "type": "target",
                "schoolSlug": None,
            },
        ],
        "edges": [
            {"source": "start", "target": "node1"},
            {"source": "node1", "target": "target"},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed School and Parcours data (idempotent)."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Seeding schools and parcours…")

        # --- Story 4.3: JSON fixture seed ---
        self._seed_from_fixture()

        # --- Story 4.7: Python-defined bac pro / terminale parcours ---
        self._seed_parcours()

    def _seed_from_fixture(self) -> None:
        """Seed from parcours_seed.json fixture (Story 4.3 data)."""
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
                f"Fixture seed done. Schools: +{schools_created} updated {schools_updated}. "
                f"Parcours: +{parcours_created} updated {parcours_updated}. "
                f"Skipped: {skipped}."
            )
        )

    def _seed_parcours(self) -> None:
        """Seed Story 4.7 parcours entries. Idempotent via update_or_create."""
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in PARCOURS_SEED:
                profession_slug = entry["profession_slug"]
                profession_defaults = entry.get("profession_defaults")

                # Get or create the profession (for test/seed environments)
                if profession_defaults:
                    profession, _ = Profession.objects.get_or_create(
                        slug=profession_slug,
                        defaults=profession_defaults,
                    )
                else:
                    try:
                        profession = Profession.objects.get(slug=profession_slug)
                    except Profession.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Parcours skipped: profession '{profession_slug}' not found."
                            )
                        )
                        continue

                # Resolve target school (may be None)
                target_school = None
                if entry.get("target_school_slug"):
                    target_school = School.objects.filter(slug=entry["target_school_slug"]).first()

                niveau = entry["niveau_scolaire"]

                # update_or_create on (profession, target_school, niveau_scolaire)
                _parcours, created = Parcours.objects.update_or_create(
                    profession=profession,
                    target_school=target_school,
                    niveau_scolaire=niveau,
                    defaults={
                        "is_default": entry.get("is_default", False),
                        "label": entry.get("label", ""),
                        "nodes": entry.get("nodes", []),
                        "edges": entry.get("edges", []),
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Story 4.7 parcours seeded: {created_count} created, {updated_count} updated. "
                f"Total bac pro parcours: "
                f"{Parcours.objects.filter(niveau_scolaire=Parcours.NiveauScolaire.TROISIEME_BAC_PRO).count()}"
            )
        )
