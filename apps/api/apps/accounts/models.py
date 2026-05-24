"""Path-Advisor User model — Story 1.3.

Roles, statuses, and consent timestamps live on the User itself. A future
`Consent` model (Story 1.9-1.13) will track per-third-party access grants;
for now we only carry the bootstrap RGPD acceptance recorded at signup.
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager
from apps.core.ids import generate_id


def _default_user_id() -> str:
    return generate_id("usr")


def _default_parental_consent_id() -> str:
    return generate_id("pcn")


def _default_parental_consent_expires_at() -> timezone.datetime:
    # 60-day window — matches the AC6 suspension job (Story 1.4 §AC1).
    return timezone.now() + timedelta(days=60)


class UserRole(models.TextChoices):
    STUDENT = "student", "Élève"
    PARENT = "parent", "Parent"
    COUNSELOR = "counselor", "Conseiller"
    SCHOOL_ADMIN = "school_admin", "Administrateur école partenaire"
    PATH_ADMIN = "path_admin", "Administrateur Path-Advisor"


class UserStatus(models.TextChoices):
    EMAIL_UNVERIFIED = "email_unverified", "Email non vérifié"
    PENDING_PARENTAL_CONSENT = "pending_parental_consent", "Consentement parental en attente"
    ACTIVE = "active", "Actif"
    SUSPENDED = "suspended", "Suspendu"
    DELETED = "deleted", "Supprimé"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_user_id,
        editable=False,
    )
    email = models.EmailField(unique=True, db_index=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    birth_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=UserStatus.choices,
        default=UserStatus.EMAIL_UNVERIFIED,
    )

    email_verified_at = models.DateTimeField(null=True, blank=True)
    consent_rgpd_at = models.DateTimeField(null=True, blank=True)
    # null is semantically distinct from "" here: it marks accounts created before
    # the CGU/RGPD prompt was introduced (none today, but the column survives a
    # future schema change without a default migration).
    consent_cgu_version = models.CharField(max_length=20, null=True, blank=True)  # noqa: DJ001

    # Multi-tenant scope. Stays null for B2C accounts; populated for B2B users (Story 1.8 RLS).
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete (Story 1.12)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        db_table = "users"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["status"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_fully_active(self) -> bool:
        """True iff the user has verified their email AND, if a minor, the parent consented.

        Frontend gates "limited mode" on this flag (Story 1.4 §AC3 / AC7). Pending-consent
        students may have `email_verified_at` set but stay `pending_parental_consent`
        until the parent decides.
        """
        return self.email_verified_at is not None and self.status == UserStatus.ACTIVE


class ParentalConsentDecision(models.TextChoices):
    GRANTED = "granted", "Autorisé"
    REFUSED = "refused", "Refusé"


class ParentalConsent(models.Model):
    """Pending or resolved parental authorization for a < 15-year-old student (Story 1.4).

    The parent has no Path-Advisor account at decision time — the URL-safe `token`
    IS the authentication for the single decision moment (cf. ADR-0003). Once Epic 6
    ships parent accounts, `parent_user_id` may be backfilled to link the two.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_parental_consent_id,
        editable=False,
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="parental_consents",
    )
    parent_email = models.EmailField()
    # Backfilled when Epic 6 ships parent self-service accounts; null otherwise.
    # NULL vs "" carries meaning here: NULL = anonymous parent (no PA account).
    parent_user_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)  # noqa: DJ001
    # `secrets.token_urlsafe(32)` → 43 base64 chars; 64 max leaves room for future schemes.
    token = models.CharField(max_length=64, unique=True, db_index=True)
    requested_at = models.DateTimeField(default=timezone.now)
    # Denormalized `requested_at + 60 days` — keeps the AC6 suspension query fast and
    # protects against clock skew on the worker that runs the Celery beat job.
    expires_at = models.DateTimeField(default=_default_parental_consent_expires_at)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    # NULL is the pending state; "granted"/"refused" are the decided states.
    decision = models.CharField(  # noqa: DJ001
        max_length=10,
        choices=ParentalConsentDecision.choices,
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    # Story 1.4 review §P26 (D1): client-supplied `accepted_at` from the parent's
    # browser. Stored alongside the server-authoritative `decided_at` so a future
    # forensic audit can compare clock drift / detect tampered clients. Validated
    # against `decided_at` with ±5 min skew tolerance at write time.
    client_accepted_at = models.DateTimeField(null=True, blank=True)
    # Story 1.4 review §P14: tracks whether the "granted" email made it out of SMTP.
    # The reconciliation task `accounts.notify_unconfirmed_granted_consents` retries
    # rows with `decision='granted' AND notification_sent_at IS NULL`.
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    # SHA-256 hex from the 8-field ConsentDialog payload (Story 1.14 review) — proves
    # exactly what content the parent saw at decision time. NULL until decision lands.
    content_hash = models.CharField(max_length=64, null=True, blank=True)  # noqa: DJ001
    # Forensic decision context — never the plain parent_email (that's hashed into the
    # audit log to comply with data minimization; cf. Story 1.4 §AC4).
    decision_ip_truncated = models.CharField(max_length=45, null=True, blank=True)  # noqa: DJ001
    decision_user_agent = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parental_consents"
        indexes: ClassVar[list[models.Index]] = [
            # Supports the Celery beat queries `decision IS NULL AND requested_at < cutoff`.
            models.Index(fields=["decision", "requested_at"]),
            models.Index(fields=["decision", "expires_at"]),
            # Supports the "find latest pending consent for student" lookup used by /resend/.
            models.Index(fields=["student", "decision"]),
        ]

    def __str__(self) -> str:
        return f"ParentalConsent(student={self.student_id} decision={self.decision or 'pending'})"

    @property
    def is_pending(self) -> bool:
        return self.decision is None

    @property
    def is_expired(self) -> bool:
        # Inclusive of the boundary: an `expires_at` equal to `now()` is past the
        # 60-day window. Story 1.4 review §P19 — eliminates a 1-second loophole.
        return self.expires_at <= timezone.now()
