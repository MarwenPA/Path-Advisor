"""Migration for Parcours model — Story 4.3.

Adds Parcours: id (UUID pk), profession FK, target_school FK,
nodes/edges JSONFields, niveau_scolaire, is_default, created_at.
"""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0001_initial"),
        ("professions", "0004_remove_profession_professions_signals_json_gin_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Parcours",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                (
                    "profession",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parcours",
                        to="professions.profession",
                    ),
                ),
                (
                    "target_school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parcours",
                        to="schools.school",
                    ),
                ),
                (
                    "nodes",
                    models.JSONField(
                        default=list,
                        help_text="List of {id, label, type, schoolId?, schoolSlug?}",
                    ),
                ),
                (
                    "edges",
                    models.JSONField(
                        default=list,
                        help_text="List of {source, target, weight?}",
                    ),
                ),
                (
                    "niveau_scolaire",
                    models.CharField(
                        blank=True,
                        help_text="e.g. lycee_1ere_tle_general, bts, but — empty = all levels",
                        max_length=50,
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "If True, this parcours is shown first for its "
                            "(profession, niveau_scolaire) pair."
                        ),
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Parcours",
                "verbose_name_plural": "Parcours",
                "ordering": ["-is_default", "niveau_scolaire"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="parcours",
            unique_together={("profession", "target_school", "niveau_scolaire")},
        ),
    ]
