"""Profession référentiel model — Story 3.2.

`Profession` holds the curated catalog of ~50 MVP occupations used by the
vocationnel scoring engine (Story 3.3). Field names use snake_case per
project conventions (implementation-patterns §Naming Patterns).

Data classification: public reference data, no PHI.
RLS: read-only for authenticated students; full CRUD for admins.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.ids import generate_id


def _default_profession_id() -> str:
    return generate_id("prof")


class ProfessionStatus(models.TextChoices):
    """Story 9.1 — editorial lifecycle of a referential entry.

    `is_active` is KEPT and synced in `save()` (`published` ⇔ True): every
    public query in epics 3/7/8 filters on it and stays untouched. `draft`
    is the only state `is_active` alone could not express.
    """

    DRAFT = "draft", "Brouillon"
    PUBLISHED = "published", "Publié"
    ARCHIVED = "archived", "Archivé"


class Profession(models.Model):
    """One curated profession in the MVP referential (50+ entries)."""

    id = models.CharField(
        default=_default_profession_id,
        editable=False,
        max_length=32,
        primary_key=True,
    )
    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=200)

    description = models.TextField(help_text="100–300 words, plain language for 15–18 year olds.")
    daily_routine = models.TextField(
        help_text="2nd-person narrative, 80–200 words. 'Tu commences ta matinée en…'"
    )
    requirements_json = models.JSONField(
        default=list,
        help_text='[{"type": "studies|skill|quality", "label": "…"}]',
    )
    prospects_text = models.TextField(help_text="At least 3 career prospects / évolutions.")
    median_salary_eur = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Annual gross median salary in EUR. NULL if unknown.",
    )
    salary_range_json = models.JSONField(
        null=True,
        blank=True,
        help_text='{"min": 22000, "max": 55000, "source": "Onisep 2025"}',
    )
    # Scoring engine uses these keywords to compute overlap with student profile.
    signals_json = models.JSONField(
        default=dict,
        help_text='{"passions": [...], "valeurs": [...], "specialites": [...], "keywords": [...]}',
    )
    # Portable JSONField (list of str) rather than postgres.ArrayField — an
    # ArrayField column can't be created on SQLite ("near '[]': syntax
    # error"), which broke the SQLite fast test lane for the WHOLE repo
    # (every django_db test builds the full schema across all apps). See
    # migration 0005 for the data-preserving conversion. GIN indexing on
    # this field was already dropped in migration 0004.
    level_compatibility = models.JSONField(
        default=list,
        help_text=(
            "Levels this profession is compatible with: college_3eme, lycee_2nde, "
            "lycee_1ere_tle_general, lycee_1ere_tle_techno, lycee_1ere_tle_pro, postbac."
        ),
    )
    sector = models.CharField(
        max_length=80,
        blank=True,
        help_text="e.g. santé, tech, social, btp, arts, business, environnement",
    )
    rome_code = models.CharField(max_length=10, blank=True, null=True)
    sources_json = models.JSONField(
        default=list,
        help_text='["Onisep", "ROME v4.0", "validation humaine 2026-06"]',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    #: Story 9.1 — editorial status; single source of truth for `is_active`.
    status = models.CharField(
        max_length=12,
        choices=ProfessionStatus.choices,
        default=ProfessionStatus.PUBLISHED,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Profession"
        verbose_name_plural = "Professions"
        indexes = [
            models.Index(fields=["is_active", "sector"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Story 9.1 — `status` drives `is_active`; the sync lives HERE so no
        # write path (admin API, shell, future importer) can desynchronise
        # the public visibility flag from the editorial state.
        self.is_active = self.status == ProfessionStatus.PUBLISHED
        if "update_fields" in kwargs and kwargs["update_fields"] is not None:
            kwargs["update_fields"] = list(set(kwargs["update_fields"]) | {"is_active"})
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Convenience helpers used by the scoring engine (Story 3.3)
    # ------------------------------------------------------------------

    def is_compatible_with_level(self, level: str) -> bool:
        return level in self.level_compatibility


def _default_report_id() -> str:
    return generate_id("rep")


class ProfessionReport(models.Model):
    """Community-sourced error report on a Profession fiche — Story 3.8.

    One student can submit multiple reports (no UNIQUE constraint — session-level
    dedup is enforced in the frontend, per 4.3 design decision).
    """

    class ErrorType(models.TextChoices):
        DESCRIPTION_INEXACTE = "description_inexacte", "Description inexacte ou trompeuse"
        DEBOUCHES_PERIMES = "debouches_perimes", "Débouchés ou informations périmées"
        LIEN_CASSE = "lien_casse", "Lien ou ressource cassé(e)"
        AUTRE = "autre", "Autre"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        RESOLVED = "resolved", "Résolu"
        DISMISSED = "dismissed", "Rejeté"

    id = models.CharField(
        default=_default_report_id,
        editable=False,
        max_length=32,
        primary_key=True,
    )
    profession = models.ForeignKey(
        Profession,
        on_delete=models.CASCADE,
        related_name="reports",
        db_index=True,
    )
    reporter = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profession_reports",
        db_index=True,
    )
    error_type = models.CharField(max_length=30, choices=ErrorType.choices)
    location = models.CharField(max_length=300, blank=True, null=True)
    comment = models.TextField(max_length=500, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Profession Report"
        verbose_name_plural = "Profession Reports"

    def __str__(self) -> str:
        return f"Report({self.error_type}) on {self.profession_id}"


def _default_revision_id() -> str:
    return generate_id("prev")


class ProfessionRevision(models.Model):
    """Story 9.1 — one snapshot per WRITE on a Profession (create, edit,
    status change, rollback). The history never rewrites itself: rolling
    back to revision N re-applies its snapshot and appends a NEW revision.
    Pattern: `StudentProfileHistory` (2.6). No RLS: the referential is
    public data, same stance as `parcoursup_milestones`.
    """

    class Action(models.TextChoices):
        CREATED = "created", "Création"
        UPDATED = "updated", "Modification"
        STATUS_CHANGED = "status_changed", "Changement de statut"
        ROLLED_BACK = "rolled_back", "Rollback"

    id = models.CharField(
        default=_default_revision_id, editable=False, max_length=32, primary_key=True
    )
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, related_name="revisions")
    #: Full editorial snapshot AFTER the write (the state this revision IS).
    snapshot = models.JSONField()
    action = models.CharField(max_length=20, choices=Action.choices)
    #: SET_NULL: an admin account deletion must not erase the history; the
    #: audit_log keeps the durable "who" (actor_id survives there).
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    #: For rollbacks: which revision was restored.
    restored_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "profession_revisions"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.profession_id} {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
