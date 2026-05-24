"""Celery sweep tests for the account-deletion pipeline (Story 1.12 §AC6)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tasks import sweep_account_deletions
from apps.accounts.tests.factories import PendingDeletionRequestFactory, UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _no_s3(monkeypatch):
    # Stub S3 purge — tests don't go to MinIO.
    monkeypatch.setattr(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        lambda user_id: (0, []),
    )


def test_sweep_hard_deletes_expired_rows():
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() - timedelta(seconds=1),
    )

    result = sweep_account_deletions()

    assert result["processed"] == 1
    assert not User.objects.filter(pk=user.id).exists()
    deletion.refresh_from_db()
    assert deletion.hard_deleted_at is not None


def test_sweep_skips_in_grace_window():
    user = UserFactory()
    PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() + timedelta(days=10),
    )

    result = sweep_account_deletions()

    assert result["processed"] == 0
    assert User.objects.filter(pk=user.id).exists()


def test_sweep_is_idempotent_same_day():
    user = UserFactory()
    PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() - timedelta(seconds=1),
    )

    sweep_account_deletions()
    second = sweep_account_deletions()

    assert second["processed"] == 0
    # Exactly one hard-delete audit row.
    assert AuditLog.objects.filter(action="gdpr.account_hard_deleted").count() == 1


def test_sweep_increments_attempt_count_on_failure():
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() - timedelta(seconds=1),
    )

    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        side_effect=RuntimeError("boto outage"),
    ):
        result = sweep_account_deletions()

    assert result["failed"] == 1
    deletion.refresh_from_db()
    assert deletion.hard_delete_attempt_count == 1
    assert deletion.last_failure_code == "RuntimeError"
    assert deletion.hard_deleted_at is None
    # Failure audit row written outside the rolled-back transaction.
    assert AuditLog.objects.filter(action="gdpr.account_hard_delete_failed").exists()


def test_sweep_gives_up_at_max_attempts(settings):
    settings.GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS = 2

    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() - timedelta(seconds=1),
        hard_delete_attempt_count=1,  # 1 prior failure
    )

    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        side_effect=RuntimeError("still down"),
    ):
        result = sweep_account_deletions()

    assert result["gave_up"] == 1
    deletion.refresh_from_db()
    assert deletion.hard_delete_attempt_count == 2
    assert AuditLog.objects.filter(action="gdpr.account_hard_delete_giving_up").exists()

    # A subsequent sweep must NOT pick this row up again.
    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        side_effect=RuntimeError("still down"),
    ):
        result2 = sweep_account_deletions()
    assert result2["candidates"] == 0
