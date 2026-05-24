"""Path-Advisor accounts models — User (Story 1.3) + GdprExportRequest (Story 1.11)."""

from __future__ import annotations

from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.ids import generate_id


def _default_user_id() -> str:
    return generate_id("usr")


def _default_gdpr_export_id() -> str:
    return generate_id("gex")


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


class GdprExportStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    IN_PROGRESS = "in_progress", "En cours"
    READY = "ready", "Prêt"
    EXPIRED = "expired", "Expiré"
    FAILED = "failed", "Échec"


class GdprExportRequest(models.Model):
    """User request to export their personal data (GDPR Article 20).

    Lifecycle: pending → in_progress → ready → expired (after GDPR_EXPORT_VALIDITY_DAYS).
    Failure path: pending → in_progress → failed (the quota does NOT consume on failure).

    The `user_id` is a logical FK (CharField, no DB constraint) so the export
    survives a hard-delete of the user account (Story 1.12) — a ready export
    remains downloadable for 7 days even if the user account is gone.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_gdpr_export_id,
        editable=False,
    )
    user_id = models.CharField(max_length=32, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=GdprExportStatus.choices,
        default=GdprExportStatus.PENDING,
        db_index=True,
    )

    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    archive_s3_key = models.CharField(max_length=512, null=True, blank=True)  # noqa: DJ001
    manifest_s3_key = models.CharField(max_length=512, null=True, blank=True)  # noqa: DJ001
    archive_sha256 = models.CharField(max_length=64, null=True, blank=True)  # noqa: DJ001
    archive_size_bytes = models.BigIntegerField(null=True, blank=True)

    # Argon2 hash of the archive password (the cleartext password is sent in the
    # second email and NEVER persisted). Used to prove possession during DPO
    # incident handling — never re-displayed to the user.
    password_hash = models.CharField(max_length=128, null=True, blank=True)  # noqa: DJ001

    error_code = models.CharField(max_length=50, null=True, blank=True)  # noqa: DJ001
    error_message = models.TextField(null=True, blank=True)  # noqa: DJ001

    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)

    # Idempotency guard for the "ready" email batch — once set, notify_export_ready
    # refuses to re-send. Cf. story §3.2 anti-pattern "don't re-send emails on
    # task replay".
    emails_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "gdpr_export_requests"
        ordering: ClassVar[list[str]] = ["-requested_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["user_id", "-requested_at"],
                name="idx_gdpr_exports_user_req",
            ),
            models.Index(
                fields=["status", "expires_at"],
                name="idx_gdpr_exports_status_exp",
            ),
        ]
        # Partial unique index — only one active (pending/in_progress) export
        # per user (post-review patch D4, 2026-05-24).
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["user_id"],
                condition=models.Q(status__in=("pending", "in_progress")),
                name="uniq_gdpr_active_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"GdprExportRequest({self.id}, user={self.user_id}, status={self.status})"

    @property
    def is_active(self) -> bool:
        """True if the request is being processed or is downloadable."""
        return self.status in (GdprExportStatus.PENDING, GdprExportStatus.IN_PROGRESS)

    @property
    def is_downloadable(self) -> bool:
        return self.status == GdprExportStatus.READY
