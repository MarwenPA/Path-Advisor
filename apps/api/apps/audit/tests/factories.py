"""Test fixtures for `AuditLog` and audit-adjacent User factories."""

from __future__ import annotations

import factory
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog, AuditResult
from apps.audit.services.hash_chain import compute_row_hash


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.test")
    role = UserRole.STUDENT
    status = UserStatus.ACTIVE
    is_active = True
    consent_rgpd_at = factory.LazyFunction(timezone.now)
    consent_cgu_version = "2026-05-15"


class PathAdminUserFactory(UserFactory):
    role = UserRole.PATH_ADMIN
    is_staff = True
    # Story 1.7 §AC10 — production path_admin users are typically superusers
    # (DPO override path). Setting it here bypasses the new `IsPathAdmin.
    # requires_mfa_verified=True` gate during tests, mirroring how a real
    # DPO who needs emergency access (no authenticator on hand) operates
    # via `manage.py shell` + superuser status.
    is_superuser = True


class AuditLogFactory(factory.django.DjangoModelFactory):
    """Direct AuditLog creation for tests — bypasses the decorator path.

    Use this when you need controlled rows (e.g. to seed a queryset). When you
    want to test the decorator/hash chain end-to-end, call the decorated
    function instead.
    """

    class Meta:
        model = AuditLog

    actor_id = "usr_test_actor"
    actor_role = "path_admin"
    subject_id = "usr_test_subject"
    action = "test.event"
    result = AuditResult.SUCCESS
    metadata = factory.LazyFunction(dict)
    prev_hash = None
    created_at = factory.LazyFunction(timezone.now)

    @factory.lazy_attribute
    def row_hash(self) -> str:
        return compute_row_hash(
            actor_id=self.actor_id,
            action=self.action,
            subject_id=self.subject_id,
            metadata=self.metadata,
            created_at=self.created_at,
            prev_hash=self.prev_hash,
        )
