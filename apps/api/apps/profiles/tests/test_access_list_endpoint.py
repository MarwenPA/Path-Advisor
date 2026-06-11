"""``GET /api/v1/profile/access-list/`` integration tests — Story 1.9 §T7.2.

Walks the real DRF view chain (`@api_view` → `permission_classes` →
serializer → audit dedup). Uses real `ParentalConsent` rows so the
`ParentalConsentSource` adapter is exercised end-to-end.
"""

from __future__ import annotations

import pytest
from allauth.account.models import EmailAddress
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import (
    ParentalConsent,
    ParentalConsentDecision,
    UserRole,
)
from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


def _make_student(email: str = "student@example.test"):
    user = UserFactory(email=email, role=UserRole.STUDENT)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


def _granted_consent(student, parent_email: str = "parent@example.test"):
    return ParentalConsent.objects.create(
        student=student,
        parent_email=parent_email,
        token="t" + parent_email,
        decision=ParentalConsentDecision.GRANTED,
        decided_at=timezone.now(),
    )


def test_anonymous_user_refused_with_401():
    """Review P14 — lock the contract. 401 for unauthenticated, 403 for wrong-role."""
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    response = client.get("/api/v1/profile/access-list/")
    assert response.status_code == 401


def test_student_with_no_grants_returns_empty_list():
    student = _make_student()
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/profile/access-list/")
    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_student_with_one_granted_consent_sees_parent_entry():
    student = _make_student()
    _granted_consent(student)

    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/profile/access-list/")

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    entry = results[0]
    assert entry["tier_type"] == "parent"
    assert entry["display_name"] == "parent@example.test"
    assert entry["id"].startswith("parental_consent:")
    assert "metiers_explores" in entry["visible_data"]
    assert "bulletins_detailles" in entry["masked_data"]
    assert entry["revocable"] is True


def test_revoked_consent_is_NOT_in_the_list():
    """A consent with `revoked_at` set MUST NOT surface."""
    student = _make_student()
    consent = _granted_consent(student, parent_email="revoked@example.test")
    consent.revoked_at = timezone.now()
    consent.save(update_fields=["revoked_at"])

    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/profile/access-list/")
    assert response.json()["results"] == []


def test_pending_consent_is_NOT_in_the_list():
    """Only `decision == 'granted'` rows surface."""
    student = _make_student()
    ParentalConsent.objects.create(
        student=student,
        parent_email="pending@example.test",
        token="t-pending",
        # decision left NULL → pending
    )
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/profile/access-list/")
    assert response.json()["results"] == []


def test_non_student_roles_receive_403():
    """Per §AC1 — parents, counselors, school_admins, path_admins, support refused."""
    for role in (
        UserRole.PARENT,
        UserRole.COUNSELOR,
        UserRole.SCHOOL_ADMIN,
        UserRole.PATH_ADMIN,
        UserRole.SUPPORT,
    ):
        user = UserFactory(email=f"{role.value}@example.test", role=role)
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        response = client.get("/api/v1/profile/access-list/")
        assert response.status_code == 403, (
            f"Role {role.value} should be refused, got {response.status_code}"
        )


def test_successful_read_writes_audit_row():
    student = _make_student()
    _granted_consent(student)

    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    # AuditLog is append-only (Story 1.13) — measure delta, not absolute count.
    before = AuditLog.objects.filter(action="profile.access_list_read").count()

    response = client.get("/api/v1/profile/access-list/")
    assert response.status_code == 200

    rows = AuditLog.objects.filter(action="profile.access_list_read").order_by("-created_at")
    assert rows.count() - before == 1, "expected exactly one audit row per successful read"
    row = rows.first()
    assert row.actor_id == str(student.id)
    assert row.subject_id == str(student.id)
    assert row.metadata["count"] == 1


def test_only_own_consents_visible_no_cross_student_leak():
    student_a = _make_student(email="a@example.test")
    student_b = _make_student(email="b@example.test")
    _granted_consent(student_a, parent_email="parent-a@example.test")
    _granted_consent(student_b, parent_email="parent-b@example.test")

    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student_a, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/profile/access-list/")
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["display_name"] == "parent-a@example.test"


def test_truncated_flag_emitted_when_cap_is_hit():
    """Review P7 / Story 1.9 §AC8 — response carries `truncated: true` when
    the aggregator hits MAX_ENTRIES."""
    from unittest.mock import patch

    student = _make_student()
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")

    # Mock aggregator to return exactly MAX_ENTRIES entries.
    from datetime import UTC, datetime

    from apps.profiles.access_list.aggregator import MAX_ENTRIES
    from apps.profiles.access_list.dto import AccessListEntry

    def _make_entry(i: int) -> AccessListEntry:
        return AccessListEntry(
            id=f"fake:{i}",
            tier_type="parent",
            display_name=f"fake-{i}@example.test",
            granted_at=datetime(2026, 1, 1, i % 24, tzinfo=UTC),
            visible_data=("metiers_explores",),
            masked_data=(),
            revocable=True,
            source_name="fake",
            source_pk=str(i),
        )

    entries = [_make_entry(i) for i in range(MAX_ENTRIES)]
    with patch(
        "apps.profiles.views.access_list.AccessListAggregator.list_for_user",
        return_value=entries,
    ):
        response = client.get("/api/v1/profile/access-list/")
    assert response.status_code == 200
    body = response.json()
    assert body["truncated"] is True
    assert len(body["results"]) == MAX_ENTRIES


def test_truncated_flag_absent_when_below_cap():
    student = _make_student()
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/profile/access-list/")
    assert response.status_code == 200
    assert "truncated" not in response.json()


def test_audit_failure_does_not_break_read_path():
    """Review P6 — record_audit raising on the read path must NOT 500 the user
    (RGPD Article 15 right to know who sees their data > audit table reliability)."""
    from unittest.mock import patch

    student = _make_student()
    _granted_consent(student)
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(student, backend="django.contrib.auth.backends.ModelBackend")

    with patch(
        "apps.profiles.views.access_list.record_audit",
        side_effect=RuntimeError("audit DB outage"),
    ):
        response = client.get("/api/v1/profile/access-list/")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
