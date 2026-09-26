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


class NewSchoolsDigestRun(models.Model):
    """Story 8.5 — one row per ISO week the digest actually ran.

    The weekly window alone is not idempotent: a manual re-run or a task
    retry within the same week would re-send the digest. This global row
    (no personal data) makes the week the unit of exactly-once, mirroring
    `ParcoursupMilestone.notified_at`'s batch-level dedup. Accepted MVP
    limitation, on record: a week with beat down is skipped, not caught up.
    """

    week = models.CharField(max_length=10, unique=True)  # ISO "2026-W39"
    sent_at = models.DateTimeField(auto_now_add=True)
    emails_queued = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "new_schools_digest_runs"

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.week}: {self.emails_queued} queued"


class DeltaRecapCursor(models.Model):
    """Story 8.6 — the "since when" reference of the DeltaRecap screen.

    NOT `User.last_login`: allauth updates that at login time, so by the
    time the front asks for the recap the reference would already be "now"
    and the delta always empty. This cursor moves only on explicit ACK
    ("Tout vu, continuer" or a card CTA click) — closing the tab without
    acking re-proposes the same deltas next time (unseen = still news).

    First GET with no row: the view creates one at `now` (baseline) and
    returns zero cards — a fresh account has no "since your last visit",
    and without this a daily user would never get a baseline at all.

    Personal data (when the student last consumed their recap) → RLS from
    migration 0005, policies mirroring `notification_preferences`.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delta_recap_cursor",
    )
    seen_at = models.DateTimeField()

    class Meta:
        db_table = "delta_recap_cursors"

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.user_id} seen_at={self.seen_at:%Y-%m-%d %H:%M}"
