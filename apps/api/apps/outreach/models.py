"""Early-outreach request model — Stories 5.4 + 5.5.

`EarlyOutreachRequest` is the central model for the rest of Epic 5 (5.6
school reception, 5.7 school response, 5.8 real-time stat propagation, 5.9
enriched history). No school-side account exists yet (Story 5.6), so
`responded`/`expired_7d` are declared for forward compatibility but
unreachable today.

Story 5.5 adds a moderation gate on the optional motivation: a request with
a non-empty `motivation_text` starts life as `pending_moderation` instead of
`pending`, and stays blocked (not visible/sendable to a school) until a
`path_admin` approves it (→ back to `pending`) or rejects it (→ `rejected`,
with `rejection_reason` set — the student can then resubmit).

Data classification: contains a student's motivation text + which school/
profession they're targeting — not health data, but personal/behavioral.
No RLS today (neither side of this relationship is tenant-scoped — B2C
student, global-reference school); revisit when Story 5.6 gives schools
their own accounts and this needs a "school only sees its own requests"
boundary.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.ids import generate_id


def _default_outreach_id() -> str:
    return generate_id("reach")


class EarlyOutreachRequestStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    PENDING_MODERATION = "pending_moderation", "Motivation en cours de relecture"
    REJECTED = "rejected", "Motivation refusée"
    RESPONDED = "responded", "École a répondu"
    EXPIRED_7D = "expired_7d", "Expiré (7 jours sans réponse)"


class EarlyOutreachRequest(models.Model):
    """One "envoi anticipé" — a student sending their profile to one school."""

    id = models.CharField(
        default=_default_outreach_id,
        editable=False,
        max_length=32,
        primary_key=True,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="early_outreach_requests",
    )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="early_outreach_requests",
    )
    # "Métier visé" — chosen by the student among THEIR OWN recommendations,
    # never a free-form pick (AC2, §2 scope decision).
    profession = models.ForeignKey(
        "professions.Profession",
        on_delete=models.PROTECT,
        related_name="early_outreach_requests",
    )
    # "Parcours sélectionné" — resolved server-side (the default Parcours
    # for profession+school if one exists), never a manual UI choice
    # (§2 scope decision, keeps the Sheet simple). Nullable: not every
    # profession/school pair has a matching Parcours row.
    parcours = models.ForeignKey(
        "schools.Parcours",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="early_outreach_requests",
    )
    motivation_text = models.TextField(
        blank=True,
        help_text=(
            "Optional free-text motivation, 200-500 words when present "
            "(Story 5.5). Gates the request into `pending_moderation` until "
            "a path_admin approves/rejects it."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=EarlyOutreachRequestStatus.choices,
        default=EarlyOutreachRequestStatus.PENDING,
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Set when `status=rejected` — explains why to the student (Story 5.5 AC).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "early_outreach_requests"
        ordering = ["-created_at"]
        indexes = [
            # Backs the monthly-quota COUNT query (student, created_at range).
            models.Index(fields=["student", "created_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"EarlyOutreachRequest({self.id}, {self.student_id} -> {self.school_id})"
