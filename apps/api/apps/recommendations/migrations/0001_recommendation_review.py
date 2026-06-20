"""Migration 0001 — RecommendationReview model (Story 3.7)."""

from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.recommendations.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("professions", "0003_profession_report"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RecommendationReview",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.recommendations.models._default_review_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("ne_correspond_pas", "Ne me correspond pas du tout"),
                            ("choquant_inapproprie", "Métier choquant ou inapproprié"),
                            ("autre", "Autre"),
                        ],
                        max_length=30,
                    ),
                ),
                ("comment", models.TextField(blank=True, max_length=500, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("resolved_correct", "Reco correcte — expliqué"),
                            ("resolved_fixed", "Modèle ajusté"),
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
                        related_name="recommendation_reviews",
                        to="professions.profession",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommendation_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Recommendation Review",
                "verbose_name_plural": "Recommendation Reviews",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="recommendationreview",
            constraint=models.UniqueConstraint(
                fields=["student", "profession"],
                name="unique_student_profession_review",
            ),
        ),
        migrations.AddIndex(
            model_name="recommendationreview",
            index=models.Index(
                fields=["status", "created_at"],
                name="recomm_status_created_idx",
            ),
        ),
    ]
