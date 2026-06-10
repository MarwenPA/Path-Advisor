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


def test_anonymous_user_refused_with_403():
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    response = client.get("/api/v1/profile/access-list/")
    assert response.status_code in {401, 403}


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
