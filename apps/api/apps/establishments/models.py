"""Establishments app models — Story 6.5.

`Establishment` — a B2B tenant (lycée/collège pilote). `Establishment.id` IS
the `tenant_id` referenced everywhere else in the repo (`User.tenant_id`,
`Cohort.tenant_id`, etc.) — cf. story §2 scope decision. This model does NOT
inherit `TenantScopedModel`: it *defines* the tenant, it is not scoped BY one.

Not to be confused with `apps.schools.models.School` — the public orientation
referential (Story 4.1), which has no `tenant_id` and is never a B2B client.

`Cohort` — a class/promotion within an `Establishment`. Inherits
`TenantScopedModel` (tenant_id/user_id/created_at/updated_at + fail-loud save).

`CohortImportJob` — async CSV-import job tracking, pattern copied from
`apps.bulletins.models.BulletinOCRJob` (Story 2.3).

`StudentImportInvitation` / `CounselorInvitation` — token-based invitation
models, pattern copied from `apps.family.models.ParentInvitation` (Story 6.1).
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.accounts.models import User
from apps.core.ids import generate_id
from apps.core.models import TenantScopedModel

_COUNSELOR_INVITATION_TTL_DAYS = 30
_STUDENT_INVITATION_TTL_DAYS = 30


def _default_counselor_invitation_expires_at():
    return timezone.now() + timedelta(days=_COUNSELOR_INVITATION_TTL_DAYS)


def _default_student_invitation_expires_at():
    return timezone.now() + timedelta(days=_STUDENT_INVITATION_TTL_DAYS)


def _default_cohort_import_job_id() -> str:
    return generate_id("cij")


def _default_cohort_id() -> str:
    return generate_id("coh")


def _default_student_import_invitation_id() -> str:
    return generate_id("sinv")


def _default_counselor_invitation_id() -> str:
    return generate_id("cinv")


class EstablishmentType(models.TextChoices):
    LYCEE = "lycee", "Lycée"
    COLLEGE = "college", "Collège"


class LicenseType(models.TextChoices):
    PILOTE_GRATUIT = "pilote_gratuit", "Pilote gratuit"
    PAYANT = "payant", "Payant"


class Establishment(models.Model):
    """A B2B tenant. `id` IS the `tenant_id` (story §2 scope decision) — no
    separate FK. Does NOT inherit `TenantScopedModel`: it defines the tenant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=EstablishmentType.choices)
    city = models.CharField(max_length=120)
    # UAI = "Unité Administrative Immatriculée" (French school registry id).
    uai = models.CharField(max_length=20, unique=True)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    license_start = models.DateField()
    license_end = models.DateField()
    license_type = models.CharField(max_length=20, choices=LicenseType.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "establishments"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"Establishment({self.id}, {self.name})"


class Cohort(TenantScopedModel):
    """A class/promotion within an `Establishment`. `tenant_id` = the parent
    establishment's `id`, set at creation by `services.cohort.create_cohort`.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_cohort_id,
        editable=False,
    )
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.CASCADE,
        related_name="cohorts",
    )
    name = models.CharField(max_length=200)
    school_year = models.CharField(max_length=20)

    class Meta:
        db_table = "cohorts"
        indexes = [
            models.Index(fields=["establishment", "school_year"]),
        ]
        constraints = [
            # Code-review fix (2026-09, closing out Story 6.5) — nothing
            # stopped a double-submit (or two admins) from creating two
            # identically-named cohorts for the same establishment/year;
            # CSV imports and counselor invitations would then silently
            # attach to whichever one the caller happened to reference.
            models.UniqueConstraint(
                fields=["establishment", "name", "school_year"],
                name="unique_cohort_per_establishment_name_year",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"Cohort({self.id}, {self.name})"


class CohortImportJobStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    PROCESSING = "processing", "En cours"
    COMPLETED = "completed", "Terminé"
    FAILED = "failed", "Échec"


class CohortImportJob(models.Model):
    """Async CSV-import job — pattern copied from `BulletinOCRJob` (Story 2.3)."""

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_cohort_import_job_id,
        editable=False,
    )
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="import_jobs")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CohortImportJobStatus.choices,
        default=CohortImportJobStatus.PENDING,
    )
    total_rows = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    # List of {"row": int, "reason": str} dicts.
    errors = models.JSONField(default=list, blank=True)
    error_message = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cohort_import_jobs"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"CohortImportJob({self.id}, {self.status})"


class StudentImportInvitationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    ACCEPTED = "accepted", "Acceptée"
    EXPIRED = "expired", "Expirée"


class StudentImportInvitation(models.Model):
    """Token-based activation link sent to a student created by CSV import.

    Pattern copied from `apps.family.models.ParentInvitation` (Story 6.1).
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_student_import_invitation_id,
        editable=False,
    )
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="student_invitations")
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_import_invitation"
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=StudentImportInvitationStatus.choices,
        default=StudentImportInvitationStatus.PENDING,
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=_default_student_invitation_expires_at)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "student_import_invitations"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"StudentImportInvitation({self.id}, {self.status})"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()


class CounselorInvitationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    ACCEPTED = "accepted", "Acceptée"
    EXPIRED = "expired", "Expirée"


class CounselorInvitation(models.Model):
    """Token-based invitation for a `role=counselor` account.

    Pattern copied from `apps.family.models.ParentInvitation` (Story 6.1).
    §4.4 anti-pattern guard: `accept_invitation` MUST use `self.email`
    exclusively — never a body-supplied email.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_counselor_invitation_id,
        editable=False,
    )
    establishment = models.ForeignKey(
        Establishment, on_delete=models.CASCADE, related_name="counselor_invitations"
    )
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=CounselorInvitationStatus.choices,
        default=CounselorInvitationStatus.PENDING,
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=_default_counselor_invitation_expires_at)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "counselor_invitations"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"CounselorInvitation({self.id}, {self.email}, {self.status})"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()


_CONSENT_COOLDOWN_DAYS = 7


class CounselorConsentStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    GRANTED = "granted", "Accordé"
    REFUSED = "refused", "Refusé"


def _default_counselor_consent_id() -> str:
    return generate_id("cnc")


class CounselorConsent(models.Model):
    """Story 6.7 — student consent gating a counselor's individual profile
    view (Story 6.8). One row per (student, counselor) pair — re-requesting
    after a refusal reuses the same row (`status` flips back to `pending`,
    subject to the 7-day cooldown below) rather than accumulating a history
    of rows.

    Deliberately NOT a `TenantScopedModel`/RLS-protected table: unlike
    `Cohort` (referential establishment data), this row's authorization is
    entirely captured by its own `student`/`counselor` FKs — the same "plain
    FK + app-layer check" choice already made for `ParentStudentLink`
    (Story 6.1) and `EarlyOutreachRequest` (Story 5.4), for the same reason
    (no shared/aggregate data at stake, just a 1:1 grant).

    `source_name = "counselor_consent"` in `apps.profiles.access_list` is a
    pre-existing seam (the visibility matrix + revoker's tier-type map
    already reference it) — this model is what plugs into it.
    """

    id = models.CharField(
        primary_key=True, max_length=32, default=_default_counselor_consent_id, editable=False
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="counselor_consents")
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requested_consents")
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="counselor_consents")
    status = models.CharField(
        max_length=10,
        choices=CounselorConsentStatus.choices,
        default=CounselorConsentStatus.PENDING,
    )
    requested_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    # Story 6.11 — surfaced to the student as "dernière consultation".
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "counselor_consents"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "counselor"], name="unique_consent_per_student_counselor"
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"CounselorConsent({self.id}, {self.student_id}, {self.status})"

    @property
    def cooldown_active(self) -> bool:
        """AC — after a refusal, the counselor may re-request once 7 days
        have passed. `decided_at` is only set on a decision, so a fresh
        (never-decided) `pending` row never triggers this."""
        if self.status != CounselorConsentStatus.REFUSED or self.decided_at is None:
            return False
        return timezone.now() < self.decided_at + timedelta(days=_CONSENT_COOLDOWN_DAYS)


def _default_counselor_note_id() -> str:
    return generate_id("cnn")


class CounselorNote(models.Model):
    """Story 6.8 AC — a counselor's private interview-prep notes on a
    student. "Visible uniquement par moi, attachées à mon compte
    conseiller, pas à l'élève" — no student-facing read path exists
    anywhere for this model; only the authoring counselor's own views
    (Story 6.8's profile/export endpoints) ever query it, always filtered
    by `counselor=request.user`.

    Same "plain FK, no RLS" choice as `CounselorConsent` — see that
    model's docstring."""

    id = models.CharField(
        primary_key=True, max_length=32, default=_default_counselor_note_id, editable=False
    )
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_notes")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "counselor_notes"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"CounselorNote({self.id}, {self.counselor_id} -> {self.student_id})"
