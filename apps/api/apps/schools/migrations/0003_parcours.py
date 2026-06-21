# Generated for Story 4.6 — Parcours model

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("professions", "0004_remove_profession_professions_signals_json_gin_and_more"),
        ("schools", "0002_admissionstat"),
    ]

    operations = [
        migrations.CreateModel(
            name="Parcours",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("nodes", models.JSONField(default=list, help_text="List of ParcoursNode dicts")),
                ("edges", models.JSONField(default=list, help_text="List of ParcoursEdge dicts")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profession",
                    models.ForeignKey(
                        blank=True,
                        null=True,
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
            ],
            options={
                "verbose_name": "Parcours",
                "verbose_name_plural": "Parcours",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["profession"], name="schools_parcours_profession_idx"),
                    models.Index(
                        fields=["target_school"], name="schools_parcours_target_school_idx"
                    ),
                ],
            },
        ),
    ]
