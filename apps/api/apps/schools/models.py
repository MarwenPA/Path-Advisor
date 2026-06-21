"""Schools & Formations referential models — Story 4.1.

`School` holds the curated catalogue of 100+ French schools used by the
parcours engine (Epic 4). `Formation` links a training program to a school
and optionally to target professions.

Data classification: public reference data, no PHI.
RLS: read-only for authenticated users; full CRUD for admins.
"""

from __future__ import annotations

from typing import ClassVar
from uuid import uuid4

from django.db import models


class School(models.Model):
    """One school / educational institution in the MVP referential."""

    class Type(models.TextChoices):
        LYCEE_PRO = "lycee_pro", "Lycée Pro"
        BTS = "bts", "BTS"
        BUT = "but", "BUT"
        IUT = "iut", "IUT"
        PREPA = "prepa", "Prépa"
        LICENCE = "licence", "Licence"
        LICENCE_PRO = "licence_pro", "Licence Pro"
        ECOLE_INGENIEUR = "ecole_ingenieur", "École d'Ingénieurs"
        ECOLE_COMMERCE = "ecole_commerce", "École de Commerce"
        ECOLE_SANTE = "ecole_sante", "École de Santé"
        UNIVERSITE = "universite", "Université"
        AUTRE = "autre", "Autre"

    class PublicPrivate(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVE_SOUS_CONTRAT = "prive_sous_contrat", "Privé sous contrat"
        PRIVE_HORS_CONTRAT = "prive_hors_contrat", "Privé hors contrat"

    SELECTIVITY_CHOICES: ClassVar = [(i, str(i)) for i in range(1, 6)]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=30, choices=Type.choices)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    tuition_min_eur = models.IntegerField(null=True, blank=True)
    tuition_max_eur = models.IntegerField(null=True, blank=True)
    apprenticeship = models.BooleanField(default=False)
    internship = models.BooleanField(default=False)
    selectivity_index = models.IntegerField(
        default=3,
        choices=SELECTIVITY_CHOICES,
        help_text="1 = très sélectif (grandes écoles), 5 = non sélectif (université ouverte)",
    )
    public_private = models.CharField(max_length=30, choices=PublicPrivate.choices)
    description = models.TextField(blank=True)
    top_debouches = models.JSONField(
        default=list,
        help_text='["Métier 1", "Métier 2", ...]',
    )
    parcoursup_dates = models.JSONField(
        default=dict,
        help_text='{"open": "2026-01-15", "close": "2026-03-10", "results": "2026-06-05"}',
    )
    affelnet_dates = models.JSONField(
        default=dict,
        help_text='{"open": "2026-01-20", "close": "2026-03-10"}',
    )
    official_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "School"
        verbose_name_plural = "Schools"
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["region"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"


class Formation(models.Model):
    """One training program / formation within a school."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=200)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="formations",
    )
    duration_years = models.IntegerField()
    parcoursup_open = models.BooleanField(default=False)
    affelnet_open = models.BooleanField(default=False)
    target_metiers = models.ManyToManyField(
        "professions.Profession",
        blank=True,
        related_name="formations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Formation"
        verbose_name_plural = "Formations"

    def __str__(self) -> str:
        return f"{self.name} @ {self.school.name}"
