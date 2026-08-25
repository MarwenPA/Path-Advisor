"""Family app models — Story 6.1.

`ParentInvitation` — a token-based invitation an élève sends to a parent
email address. Copies the token/expiry pattern of `ParentalConsent`
(Story 1.4) but is a DISTINCT model: a `ParentalConsent` is a legal
decision by a parent who never gets an account; a `ParentInvitation`
always leads (on acceptance) to a real `User(role="parent")` account.
Do NOT merge the two (cf. story §4.2).

`ParentStudentLink` — the many-to-many link table between a parent `User`
and a student `User`. A parent can follow several children (fratrie); a
student can have several linked parents (mère + père, or parent + tuteur).
The partial unique index on `(parent, student) WHERE revoked_at IS NULL`
prevents duplicate *active* links while preserving revocation history for
audit (Story 1.9's `granted_at` + RGPD forensics).
"""

from __future__ import annotations

from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.core.ids import generate_id


def _default_invitation_id() -> str:
    return generate_id("pinv")


def _default_link_id() -> str:
    return generate_id("plnk")


def _default_invitation_expires_at():
    # 30-day TTL — story §T1.1 / AC1.
    return timezone.now() + timedelta(days=30)


class ParentRelationship(models.TextChoices):
    MERE = "mere", "Mère"
    PERE = "pere", "Père"
    TUTEUR = "tuteur", "Tuteur"
    AUTRE = "autre", "Autre"


class ParentInvitationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    ACCEPTED = "accepted", "Acceptée"
    EXPIRED = "expired", "Expirée"
    REVOKED = "revoked", "Révoquée"


class ParentInvitation(models.Model):
    """Pending or resolved invitation from a student to a parent (Story 6.1)."""

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_invitation_id,
        editable=False,
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_parent_invitations",
    )
    parent_email = models.EmailField()
    relationship = models.CharField(
        max_length=10,
        choices=ParentRelationship.choices,
        null=True,
        blank=True,
    )
    custom_message = models.CharField(max_length=200, null=True, blank=True)
    # `secrets.token_urlsafe(32)` → 43 base64 chars, matching the Story 1.4 pattern.
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=ParentInvitationStatus.choices,
        default=ParentInvitationStatus.PENDING,
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=_default_invitation_expires_at)
    accepted_at = models.DateTimeField(null=True, blank=True)
    # Parity with the Story 1.4 pattern — unused by the MVP resend flow (T2.4
    # rate-limits via cache, not this field) but avoids a future migration if
    # a scheduled reminder job is added later (cf. story §T1.1).
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    # Denormalized from `student.tenant_id` — B2C students have `tenant_id=None`.
    # Cf. AC7 second clause: scoping by `student_id` is sufficient, no RLS needed.
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["parent_email", "status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"ParentInvitation({self.id}, {self.parent_email}, {self.status})"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()


class ParentStudentLink(models.Model):
    """Active or revoked link between a parent `User` and a student `User`."""

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_link_id,
        editable=False,
    )
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="parent_links",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="student_links",
    )
    relationship = models.CharField(
        max_length=10,
        choices=ParentRelationship.choices,
        null=True,
        blank=True,
    )
    linked_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # T1.2 — partial unique index: at most one ACTIVE link per
            # (parent, student) pair. A revoked link does not block re-linking.
            models.UniqueConstraint(
                fields=["parent", "student"],
                condition=Q(revoked_at__isnull=True),
                name="uniq_active_parent_student_link",
            )
        ]
        indexes = [
            models.Index(fields=["student", "revoked_at"]),
            models.Index(fields=["parent", "revoked_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"ParentStudentLink({self.parent_id} -> {self.student_id})"
