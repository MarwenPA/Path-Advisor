"""Initial migration for Profession model — Story 3.2."""

import django.contrib.postgres.fields
from django.db import migrations, models

import apps.professions.models


class Migration(migrations.Migration):
    initial = True

    dependencies: list = []

    operations = [
        migrations.CreateModel(
            name="Profession",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.professions.models._default_profession_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("name", models.CharField(max_length=200)),
                (
                    "description",
                    models.TextField(
                        help_text="100–300 words, plain language for 15–18 year olds."
                    ),
                ),
                (
                    "daily_routine",
                    models.TextField(
                        help_text="2nd-person narrative, 80–200 words. 'Tu commences ta matinée en…'"
                    ),
                ),
                (
                    "requirements_json",
                    models.JSONField(
                        default=list,
                        help_text='[{"type": "studies|skill|quality", "label": "…"}]',
                    ),
                ),
                (
                    "prospects_text",
                    models.TextField(help_text="At least 3 career prospects / évolutions."),
                ),
                (
                    "median_salary_eur",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        help_text="Annual gross median salary in EUR. NULL if unknown.",
                    ),
                ),
                (
                    "salary_range_json",
                    models.JSONField(
                        blank=True,
                        null=True,
                        help_text='{"min": 22000, "max": 55000, "source": "Onisep 2025"}',
                    ),
                ),
                (
                    "signals_json",
                    models.JSONField(
                        default=dict,
                        help_text='{"passions": [...], "valeurs": [...], "specialites": [...], "keywords": [...]}',
                    ),
                ),
                (
                    "level_compatibility",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=40),
                        default=list,
                        help_text=(
                            "Levels this profession is compatible with: college_3eme, lycee_2nde, "
                            "lycee_1ere_tle_general, lycee_1ere_tle_techno, lycee_1ere_tle_pro, postbac."
                        ),
                        size=None,
                    ),
                ),
                (
                    "sector",
                    models.CharField(
                        blank=True,
                        max_length=80,
                        help_text="e.g. santé, tech, social, btp, arts, business, environnement",
                    ),
                ),
                ("rome_code", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "sources_json",
                    models.JSONField(
                        default=list,
                        help_text='["Onisep", "ROME v4.0", "validation humaine 2026-06"]',
                    ),
                ),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Profession",
                "verbose_name_plural": "Professions",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="profession",
            index=models.Index(
                fields=["is_active", "sector"],
                name="professions_is_acti_sector_idx",
            ),
        ),
    ]
