"""Story 1.3 ↔ 1.13 integration — verify the decorated services persist audit rows."""

from __future__ import annotations

import pytest
from django.utils import timezone

from apps.accounts.models import UserStatus
from apps.accounts.services.auth_service import mark_email_verified, record_signup_event
from apps.audit.models import AuditLog, AuditResult
from apps.audit.tests.factories import UserFactory


@pytest.mark.django_db
def test_signup_persists_audit_log_via_decorator():
    user = UserFactory(
        status=UserStatus.EMAIL_UNVERIFIED, consent_cgu_version="2026-05-15"
    )

    record_signup_event(user=user)

    rows = AuditLog.objects.filter(action="user.signed_up")
    assert rows.count() == 1
    row = rows.first()
    assert row.result == AuditResult.SUCCESS
    assert row.subject_id == user.id
    assert row.metadata == {
        "role": user.role,
        "status": user.status,
        "consent_cgu_version": "2026-05-15",
    }


@pytest.mark.django_db
def test_email_verified_persists_audit_log_via_decorator():
    user = UserFactory(
        status=UserStatus.EMAIL_UNVERIFIED,
        email_verified_at=None,
    )

    mark_email_verified(user)

    rows = AuditLog.objects.filter(action="user.email_verified")
    assert rows.count() == 1
    row = rows.first()
    assert row.result == AuditResult.SUCCESS
    assert row.subject_id == user.id
    assert row.metadata == {"role": user.role}


@pytest.mark.django_db
def test_email_verified_is_idempotent_and_still_audits():
    user = UserFactory(status=UserStatus.ACTIVE, email_verified_at=timezone.now())

    mark_email_verified(user)
    mark_email_verified(user)

    # Each call still produces an audit row even though the service early-returns.
    assert AuditLog.objects.filter(action="user.email_verified").count() == 2
