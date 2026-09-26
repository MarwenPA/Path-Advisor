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
