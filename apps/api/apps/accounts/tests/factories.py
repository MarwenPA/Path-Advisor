"""factory_boy fixtures for the accounts app — Story 1.3."""

from __future__ import annotations

from datetime import date, timedelta

import factory
from django.utils import timezone

from apps.accounts.models import (
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
    archive_s3_key = factory.LazyAttribute(
        lambda obj: f"gdpr-exports/{obj.user_id}/{obj.id}.zip"
    )
    archive_size_bytes = 1024
    archive_sha256 = "0" * 64
    password_hash = "argon2$dummy$hash"
