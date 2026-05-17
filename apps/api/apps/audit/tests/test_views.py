"""DPO endpoints — permission gating, meta-audit, filtering, CSV export."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.audit.models import AuditLog, AuditResult
from apps.audit.tests.factories import AuditLogFactory, PathAdminUserFactory, UserFactory


@pytest.mark.django_db
def test_audit_logs_endpoint_returns_403_for_non_path_admin():
    student = UserFactory()
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.get("/api/v1/audit/logs/")

    assert response.status_code == 403
    # The refusal itself must be audited (FR12 meta-audit on the denied path).
    denied = AuditLog.objects.filter(action="audit.log_query_denied")
    assert denied.count() == 1
    assert denied.first().result == AuditResult.DENIED


@pytest.mark.django_db
def test_audit_logs_endpoint_returns_403_for_anonymous():
    client = APIClient()
    response = client.get("/api/v1/audit/logs/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_audit_logs_endpoint_returns_filtered_results_for_path_admin():
    AuditLogFactory.create(action="outreach.profile_sent", subject_id="usr_alpha")
    AuditLogFactory.create(action="user.signed_up", subject_id="usr_beta")
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/audit/logs/?action=outreach.profile_sent")

    assert response.status_code == 200
    body = response.json()
    results = body.get("results", body) if isinstance(body, dict) else body
    # The list view itself records `audit.log_queried`; filter on the seeded action.
    actions_in_results = [r["action"] for r in results]
    assert "outreach.profile_sent" in actions_in_results
    assert "user.signed_up" not in actions_in_results


@pytest.mark.django_db
def test_audit_logs_endpoint_query_is_itself_audited():
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    client.get("/api/v1/audit/logs/?subject_id=usr_xyz")

    audited = AuditLog.objects.filter(action="audit.log_queried")
    assert audited.count() == 1
    assert audited.first().metadata["filters"].get("subject_id") == "usr_xyz"


@pytest.mark.django_db
def test_audit_logs_endpoint_filters_by_action_prefix():
    AuditLogFactory.create(action="outreach.profile_sent")
    AuditLogFactory.create(action="outreach.school_responded")
    AuditLogFactory.create(action="user.signed_up")
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/audit/logs/?action=outreach.")

    body = response.json()
    results = body.get("results", body) if isinstance(body, dict) else body
    actions_in_results = {r["action"] for r in results}
    assert "outreach.profile_sent" in actions_in_results
    assert "outreach.school_responded" in actions_in_results
    assert "user.signed_up" not in actions_in_results


@pytest.mark.django_db
def test_audit_logs_endpoint_rejects_invalid_tenant_id():
    """Bogus tenant_id should produce a typed 400 Problem, not a 500."""
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/audit/logs/?tenant_id=not-a-uuid")

    assert response.status_code == 400
    body = response.json()
    assert body.get("type", "").endswith("/invalid-filter")


@pytest.mark.django_db
def test_audit_logs_endpoint_403_returns_rfc7807_problem_details():
    """Non-`path_admin` must get the typed `insufficient-permissions` Problem (Story 1.13 §AC5)."""
    student = UserFactory()
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.get("/api/v1/audit/logs/")

    assert response.status_code == 403
    assert response["Content-Type"].startswith("application/problem+json")
    body = response.json()
    assert body.get("type", "").endswith("/insufficient-permissions")
    assert body.get("status") == 403


@pytest.mark.django_db
def test_audit_logs_export_csv_returns_text_csv_content_type():
    AuditLogFactory.create(action="export.test")
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/audit/logs/export.csv")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "attachment" in response.get("Content-Disposition", "")


@pytest.mark.django_db
def test_audit_logs_export_csv_below_threshold_is_synchronous():
    AuditLogFactory.create(action="export.sync")
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    with patch("apps.audit.views.export_csv_to_s3.delay") as delay_mock:
        response = client.get("/api/v1/audit/logs/export.csv")

    assert response.status_code == 200
    assert not delay_mock.called


@pytest.mark.django_db
def test_audit_logs_export_csv_above_threshold_returns_202_and_enqueues_celery_task(settings):
    settings.AUDIT_EXPORT_SYNC_THRESHOLD = 0  # force async path
    AuditLogFactory.create(action="export.async")
    admin = PathAdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=admin)

    with patch("apps.audit.views.export_csv_to_s3.delay") as delay_mock:
        response = client.get("/api/v1/audit/logs/export.csv")

    assert response.status_code == 202
    assert delay_mock.called
