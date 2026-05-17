"""Path-Advisor User model — Story 1.3.

Roles, statuses, and consent timestamps live on the User itself. A future
`Consent` model (Story 1.9-1.13) will track per-third-party access grants;
for now we only carry the bootstrap RGPD acceptance recorded at signup.
"""

from __future__ import annotations

from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.ids import generate_id


def _default_user_id() -> str:
    return generate_id("usr")


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
