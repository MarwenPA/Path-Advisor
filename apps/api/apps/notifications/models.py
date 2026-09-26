"""Story 8.2 — per-user notification preferences (opt-out model).

First Epic-8 table holding personal data → RLS from the initial migration,
policies mirrored from `students/0001_initial` (the 1.16 lane exercises
them for real in CI now).

Opt-out semantics, deliberately: **no row means enabled**. The four
categories are product notifications the epic's later stories send by
default; unsubscribing writes `enabled=False`, re-subscribing is an
explicit act (AC3). The engine (`services.notify`) is the single
enforcement point — a category email that bypasses it cannot exist,
because sending goes through `send_transactional` with the legal footer
links only the engine injects.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class NotificationCategory(models.TextChoices):
    PARCOURSUP_CALENDAR = "parcoursup_calendar", "Calendrier Parcoursup"
    SCHOOL_RESPONSES = "school_responses", "Réponses école"
    NEW_SCHOOLS = "new_schools", "Nouvelles écoles pertinentes"
    PROFILE_COMPLETION = "profile_completion", "Rappels de complétion profil"


class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    category = models.CharField(max_length=32, choices=NotificationCategory.choices)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"
        constraints = [
            models.UniqueConstraint(fields=["user", "category"], name="uniq_user_category"),
        ]

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.user_id}:{self.category}={'on' if self.enabled else 'off'}"


def is_enabled(user_id: str, category: str) -> bool:
    """Effective state: absence of a row = enabled (opt-out model)."""
    return not NotificationPreference.objects.filter(
        user_id=user_id, category=category, enabled=False
    ).exists()


class MilestoneKind(models.TextChoices):
    """The five standard Parcoursup milestones (Story 8.3 AC2)."""

    OUVERTURE = "ouverture", "Ouverture Parcoursup"
    J30_FERMETURE_VOEUX = "j30_fermeture_voeux", "J-30 fermeture des vœux"
    FERMETURE_VOEUX = "fermeture_voeux", "Fermeture des vœux"
    RESULTATS_PRINCIPALE = "resultats_principale", "Résultats phase principale"
    RESULTATS_COMPLEMENTAIRE = "resultats_complementaire", "Résultats phase complémentaire"


class ParcoursupMilestone(models.Model):
    """Story 8.3 — a global campaign date, known in advance.

    No RLS on purpose: these are public calendar facts (no personal data).
    "Configuration admin" is the idempotent `seed_parcoursup_calendar`
    command for now; a visual CRUD belongs to Epic 9.

    `notified_at` is the batch-level dedup: the daily beat task sends each
    milestone exactly once, and marks it inside the same transaction as the
    outbox rows (crash before commit = nothing sent AND nothing marked).
    """

    kind = models.CharField(max_length=32, choices=MilestoneKind.choices)
    campaign = models.CharField(max_length=16)  # e.g. "2026-2027"
    date = models.DateField()
    #: How many days ahead the notification goes out (0 = on the day).
    notify_days_before = models.PositiveSmallIntegerField(default=0)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "parcoursup_milestones"
        constraints = [
            models.UniqueConstraint(fields=["kind", "campaign"], name="uniq_kind_campaign"),
        ]

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.campaign} {self.kind} @ {self.date} (J-{self.notify_days_before})"
