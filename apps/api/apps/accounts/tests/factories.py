"""factory_boy fixtures for the accounts app — Story 1.3."""

from __future__ import annotations

import secrets
from datetime import date, timedelta

import factory
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.accounts.models import (
    AccountDeletionRequest,
    GdprExportRequest,
    GdprExportStatus,
    User,
    UserRole,
    UserStatus,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.test")
    role = UserRole.STUDENT
    birth_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365 * 18)
    )  # 18 years old
    status = UserStatus.ACTIVE
    email_verified_at = factory.LazyFunction(timezone.now)
    consent_rgpd_at = factory.LazyFunction(timezone.now)
    consent_cgu_version = "2026-05-15"
    is_active = True

    @factory.post_generation
    def password(self, create: bool, extracted: str | None, **kwargs) -> None:
        password = extracted or "Path-Advisor-2026!"
        self.set_password(password)
        if create:
            self.save(update_fields=["password"])


class EmailUnverifiedUserFactory(UserFactory):
    status = UserStatus.EMAIL_UNVERIFIED
    email_verified_at = None


class MinorUserFactory(UserFactory):
    birth_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365 * 13)
    )  # 13 years old


class GdprExportRequestFactory(factory.django.DjangoModelFactory):
    """Default: a `pending` request. Use traits for other states."""

    class Meta:
        model = GdprExportRequest

    status = GdprExportStatus.PENDING

    @factory.lazy_attribute
    def user_id(self) -> str:
        # The model carries a CharField (logical FK, no DB constraint) so a
        # plain SubFactory(UserFactory) would assign the User instance rather
        # than its id. lazy_attribute lets us materialise the user and grab .id.
        return UserFactory().id


class ReadyGdprExportFactory(GdprExportRequestFactory):
    status = GdprExportStatus.READY
    ready_at = factory.LazyFunction(timezone.now)
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    archive_s3_key = factory.LazyAttribute(lambda obj: f"gdpr-exports/{obj.user_id}/{obj.id}.zip")
    archive_size_bytes = 1024
    archive_sha256 = "0" * 64
    password_hash = "argon2$dummy$hash"


class DeletedUserFactory(UserFactory):
    """Post-soft-delete state — status=DELETED, is_active=False."""

    status = UserStatus.DELETED
    is_active = False
    deleted_at = factory.LazyFunction(timezone.now)


class PendingDeletionRequestFactory(factory.django.DjangoModelFactory):
    """Default: in-flight deletion request (cancelled_at IS NULL, hard_deleted_at IS NULL).

    Useful for testing both the cancel endpoint (still in grace window) and the
    sweep (when `hard_delete_after` is overridden to a past timestamp).
    """

    class Meta:
        model = AccountDeletionRequest

    user = factory.SubFactory(UserFactory)
    user_id_snapshot = factory.LazyAttribute(lambda obj: str(obj.user.id))
    cancel_token = factory.LazyFunction(lambda: secrets.token_urlsafe(32))
    requested_at = factory.LazyFunction(timezone.now)
    hard_delete_after = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=30),
    )
    password_hash_at_request = factory.LazyFunction(
        lambda: make_password("Path-Advisor-2026!"),
    )


class HardDeletedDeletionRequestFactory(PendingDeletionRequestFactory):
    """Terminal-state row used to assert idempotency of the sweep."""

    hard_deleted_at = factory.LazyFunction(timezone.now)
    user = None  # post-cascade row — FK is SET_NULL
