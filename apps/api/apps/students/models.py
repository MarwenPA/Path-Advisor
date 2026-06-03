"""Student onboarding profile — Story 2.1.

`StudentProfile` carries the declarative signals the recommendation engine
(Epic 3) crosses with bulletins (Epic 2 step 3) to produce vocational scores.

The profile is created lazily on first PATCH (signal-free) so the row only
exists when the student starts answering step 1 — not at signup time. This
keeps the table small and avoids backfilling empty rows when accounts are
created in bulk (B2B onboarding, Epic 6).

Tenant isolation (Story 1.8): `tenant_id` is denormalized from `user.tenant_id`
so the RLS policy can filter without joining. Auto-synced in `save()`.
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.db import models
from django.utils import timezone

from apps.core.ids import generate_id


def _default_profile_id() -> str:
    return generate_id("sprf")


def _default_interets() -> dict[str, str | None]:
    """JSONB default: three nullable free-form fields (AC4)."""
    return {"1": None, "2": None, "3": None}


class OnboardingStep1Status(models.TextChoices):
    """Per AC7 / AC10 — lifecycle of step-1 completion.

    `pending`         — row exists but no PATCH yet (rare — created by GET in
                        rare race conditions; usually the row is created on
                        first PATCH).
    `in_progress`     — at least one sub-step PATCH'd but not all three.
    `completed`       — all three sub-steps validated, redirect to step-2.
    `skipped`         — user clicked "Plus tard" with nothing or partial data.
                        Distinct from `completed` so the maturité-de-profil
                        score (Story 2.7) can weight it differently.
    `partial_skipped` — sub-step(s) completed AND user skipped the rest.
                        AC7 edge case #1: 1A+1B completed, "Plus tard" on 1C.
    """

    PENDING = "pending", "En attente"
    IN_PROGRESS = "in_progress", "En cours"
    COMPLETED = "completed", "Terminé"
    SKIPPED = "skipped", "Reporté"
    PARTIAL_SKIPPED = "partial_skipped", "Partiellement reporté"


class StudentProfile(models.Model):
    """Per-student declarative profile populated by onboarding step 1 (Story 2.1).

    JSONB columns are used instead of normalized join tables because:
    - Cardinality is small and bounded (≤ 8 passions, ≤ 5 valeurs, 3 intérêts).
    - Read pattern is always "the whole profile of one user" — no cross-row
      analytical queries on individual IDs (the scoring engine in Epic 3
      consumes the whole array as a feature vector).
    - Migration cost of adding a new field is zero (PATCH ships the new key).

    Validation against the curated referential lives in `serializers.py` and
    `apps.students.onboarding.referentials`. The DB column accepts arbitrary
    JSON shape — by design (forward compatibility with custom: passions and
    future fields).
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_profile_id,
        editable=False,
    )
    # OneToOne with User: a single profile per student. CASCADE so a hard-deleted
    # user (Story 1.12) drops their profile too — consistent with the GDPR
    # right-to-erasure semantics.
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    # Denormalized from user.tenant_id for the RLS policy (see Story 1.8 pattern
    # on parental_consents). Auto-synced in `save()`.
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    # AC2 — passions as JSONB array of string IDs. Max 8 enforced at serializer
    # layer (a DB check constraint would block partial PATCH sequences).
    passions = models.JSONField(default=list, blank=True)
    # AC3 — valeurs as JSONB array, 3-5 entries at validated completion.
    valeurs = models.JSONField(default=list, blank=True)
    # AC4 — three nullable free-form intérêt slots.
    interets = models.JSONField(default=_default_interets, blank=True)

    onboarding_step1_status = models.CharField(
        max_length=20,
        choices=OnboardingStep1Status.choices,
        default=OnboardingStep1Status.PENDING,
        db_index=True,
    )
    onboarding_step1_completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profiles"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["onboarding_step1_status"]),
        ]

    def __str__(self) -> str:
        return f"StudentProfile({self.id}, user={self.user_id}, step1={self.onboarding_step1_status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Story 1.8 pattern — keep tenant_id consistent with the user's tenant
        # so the RLS policy can filter without joining. Explicit caller value
        # wins (mirrors ParentalConsent.save).
        if self.tenant_id is None and self.user_id:
            user_tenant = (
                type(self)
                .user.field.related_model.objects.filter(pk=self.user_id)
                .values_list("tenant_id", flat=True)
                .first()
            )
            self.tenant_id = user_tenant
        super().save(*args, **kwargs)

    @property
    def is_step1_completed(self) -> bool:
        return self.onboarding_step1_status == OnboardingStep1Status.COMPLETED

    def mark_completed(self) -> None:
        """Set status=completed + stamp the completion timestamp.

        Idempotent: calling this on an already-completed profile is a no-op
        (the timestamp does not move). The 2nd-time-through case is realistic
        because AC10 redirects completed users away from /onboarding/step-1
        but a stale tab POST may still hit the endpoint.
        """
        if self.is_step1_completed:
            return
        self.onboarding_step1_status = OnboardingStep1Status.COMPLETED
        self.onboarding_step1_completed_at = timezone.now()

    def mark_skipped(self, *, partial: bool) -> None:
        """Set status=skipped or partial_skipped per AC7 edge case #1.

        `partial=True` if at least one sub-step had been validated before the
        skip click — caller is responsible for that determination since it
        depends on the in-flight payload.
        """
        self.onboarding_step1_status = (
            OnboardingStep1Status.PARTIAL_SKIPPED if partial else OnboardingStep1Status.SKIPPED
        )
