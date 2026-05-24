"""Story 1.11 — REST surface for /api/v1/me/gdpr-exports."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status as drf_status
from rest_framework.test import APIClient

from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_export_requires_authentication(api_client):
    response = api_client.post("/api/v1/me/gdpr-exports/")
    assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_export_returns_202_and_creates_pending_row(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    with patch("apps.accounts.tasks.build_export.delay"):
        response = api_client.post("/api/v1/me/gdpr-exports/")

    assert response.status_code == drf_status.HTTP_202_ACCEPTED, response.content
    body = response.json()
    assert body["status"] == "pending"
    assert body["id"].startswith("gex_")
    assert GdprExportRequest.objects.filter(id=body["id"], user_id=user.id).exists()


@pytest.mark.django_db
def test_create_export_409_when_active_request_exists(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    GdprExportRequest.objects.create(user_id=user.id, status=GdprExportStatus.PENDING)

    response = api_client.post("/api/v1/me/gdpr-exports/")
    assert response.status_code == drf_status.HTTP_409_CONFLICT
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/gdpr-export-in-progress"


@pytest.mark.django_db
def test_create_export_429_when_rate_limited(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now() - timedelta(hours=2),
        expires_at=timezone.now() + timedelta(days=7),
    )

    response = api_client.post("/api/v1/me/gdpr-exports/")
    assert response.status_code == drf_status.HTTP_429_TOO_MANY_REQUESTS
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/gdpr-export-rate-limited"
    assert "Retry-After" in response.headers


@pytest.mark.django_db
def test_list_only_returns_own_exports(api_client):
    me = UserFactory()
    other = UserFactory()
    GdprExportRequest.objects.create(user_id=me.id)
    GdprExportRequest.objects.create(user_id=other.id)

    api_client.force_authenticate(user=me)
    response = api_client.get("/api/v1/me/gdpr-exports/")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"].startswith("gex_")


@pytest.mark.django_db
def test_retrieve_other_users_export_returns_404(api_client):
    other = UserFactory()
    me = UserFactory()
    export = GdprExportRequest.objects.create(user_id=other.id)
    api_client.force_authenticate(user=me)
    response = api_client.get(f"/api/v1/me/gdpr-exports/{export.id}/")
    assert response.status_code == drf_status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_404_when_not_ready(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    export = GdprExportRequest.objects.create(
        user_id=user.id, status=GdprExportStatus.IN_PROGRESS
    )
    response = api_client.get(f"/api/v1/me/gdpr-exports/{export.id}/download/")
    assert response.status_code == drf_status.HTTP_404_NOT_FOUND
    assert response.json()["type"] == "https://path-advisor.fr/errors/gdpr-export-not-ready"


@pytest.mark.django_db
def test_download_410_when_expired(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    export = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.EXPIRED,
    )
    response = api_client.get(f"/api/v1/me/gdpr-exports/{export.id}/download/")
    assert response.status_code == drf_status.HTTP_410_GONE


@pytest.mark.django_db
def test_download_302_increments_counter_and_audits(api_client, fake_s3, settings):
    from apps.audit.models import AuditLog

    user = UserFactory()
    api_client.force_authenticate(user=user)
    key = f"gdpr-exports/{user.id}/test.zip"
    export = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
        archive_s3_key=key,
        archive_size_bytes=1024,
    )

    response = api_client.get(f"/api/v1/me/gdpr-exports/{export.id}/download/")
    assert response.status_code == drf_status.HTTP_302_FOUND
    assert "fake-s3.test" in response["Location"]
    assert f"X-Amz-Expires={settings.GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS}" in response["Location"]

    export.refresh_from_db()
    assert export.download_count == 1
    assert export.last_downloaded_at is not None
    assert AuditLog.objects.filter(
        action="gdpr.export_downloaded",
        subject_id=user.id,
    ).exists()


@pytest.mark.django_db
def test_download_403_when_cap_reached(api_client, fake_s3, settings):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    export = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
        archive_s3_key=f"gdpr-exports/{user.id}/x.zip",
        download_count=settings.GDPR_EXPORT_MAX_DOWNLOADS,
    )
    response = api_client.get(f"/api/v1/me/gdpr-exports/{export.id}/download/")
    assert response.status_code == drf_status.HTTP_403_FORBIDDEN
    assert response.json()["type"] == "https://path-advisor.fr/errors/gdpr-export-download-cap"
