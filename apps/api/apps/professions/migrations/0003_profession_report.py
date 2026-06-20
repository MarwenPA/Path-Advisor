"""Add ProfessionReport model — Story 3.8."""

from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.professions.models


class Migration(migrations.Migration):
    dependencies = [
        ("professions", "0002_profession_gin_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfessionReport",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.professions.models._default_report_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "error_type",
                    models.CharField(
                        choices=[
                            ("description_inexacte", "Description inexacte ou trompeuse"),
                            ("debouches_perimes", "Débouchés ou informations périmées"),
                            ("lien_casse", "Lien ou ressource cassé(e)"),
                            ("autre", "Autre"),
                        ],
                        max_length=30,
                    ),
                ),
                ("location", models.CharField(blank=True, max_length=300, null=True)),
                ("comment", models.TextField(blank=True, max_length=500, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("resolved", "Résolu"),
                            ("dismissed", "Rejeté"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "profession",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports",
                        to="professions.profession",
                    ),
                ),
                (
                    "reporter",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="profession_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Profession Report",
                "verbose_name_plural": "Profession Reports",
                "ordering": ["-created_at"],
            },
        ),
    ]
