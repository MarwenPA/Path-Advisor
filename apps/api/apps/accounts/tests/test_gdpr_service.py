"""Story 1.11 — GdprExportService.request_export."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.accounts.gdpr_exceptions import (
    GdprExportInProgress,
    GdprExportRateLimited,
)
from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.services.gdpr_service import GdprExportService
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_request_export_creates_pending_row_and_dispatches_task():
    user = UserFactory()
    # `transaction.on_commit` does not fire inside the implicit pytest-django
    # transaction; `captureOnCommitCallbacks` forces them to flush.
    case = TestCase()
    with (
        patch("apps.accounts.tasks.build_export.delay") as mock_delay,
        case.captureOnCommitCallbacks(execute=True),
    ):
        export = GdprExportService.request_export(user=user)

    assert export.pk is not None
    assert export.status == GdprExportStatus.PENDING
    assert export.user_id == user.id
    mock_delay.assert_called_once_with(export_id=export.id)


@pytest.mark.django_db
def test_request_export_refuses_concurrent_active_request():
    user = UserFactory()
    GdprExportRequest.objects.create(user_id=user.id, status=GdprExportStatus.PENDING)
    with pytest.raises(GdprExportInProgress):
        GdprExportService.request_export(user=user)


@pytest.mark.django_db
def test_request_export_refuses_when_within_rate_limit_window():
    user = UserFactory()
    # A recent `ready` export inside the rate-limit window.
    GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now() - timedelta(hours=2),
        expires_at=timezone.now() + timedelta(days=7),
    )
    with pytest.raises(GdprExportRateLimited) as ex:
        GdprExportService.request_export(user=user)
    assert ex.value.extras.get("retry_after_seconds", 0) > 0


@pytest.mark.django_db
def test_request_export_allows_after_rate_limit_window_elapsed():
    user = UserFactory()
    # A `ready` export from 25 hours ago — outside the 24h window.
    GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now() - timedelta(hours=25),
        expires_at=timezone.now() - timedelta(hours=1),
    )
    with patch("apps.accounts.tasks.build_export.delay"):
        export = GdprExportService.request_export(user=user)
    assert export.status == GdprExportStatus.PENDING


@pytest.mark.django_db
def test_failed_export_does_not_consume_quota():
    user = UserFactory()
    GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.FAILED,
        ready_at=timezone.now() - timedelta(minutes=5),
    )
    with patch("apps.accounts.tasks.build_export.delay"):
        export = GdprExportService.request_export(user=user)
    assert export.status == GdprExportStatus.PENDING
