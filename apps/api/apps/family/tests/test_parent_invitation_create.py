"""Story 6.1 — T8.1: create + resend + duplicate-pending (AC1/AC2)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog
from apps.core.rls import bypass_rls
from apps.family.models import ParentInvitation, ParentInvitationStatus

pytestmark = [pytest.mark.django_db, pytest.mark.postgresql_only]


def _uf(**kwargs):
    # `users` has FORCE RLS (Story 1.8) — test-setup writes go through the
    # sanctioned bypass helper (same pattern as apps/billing/tests/test_api.py).
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _create_url() -> str:
    return reverse("family:parent-invitation-collection")


def _client_for(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_create_invitation_happy_path_returns_201_and_pending_status():
    student = _uf()
    client = _client_for(student)

    response = client.post(
        _create_url(),
        {"parent_email": "parent@example.test", "relationship": "mere"},
        format="json",
    )

    assert response.status_code == 201, response.content
    body = response.json()
    assert body["status"] == ParentInvitationStatus.PENDING
    assert body["parent_email"] == "parent@example.test"

    invitation = ParentInvitation.objects.get(id=body["id"])
    assert invitation.student_id == student.id
    assert len(invitation.token) >= 32
    assert AuditLog.objects.filter(action="parent_invitation.created").exists()


def test_create_invitation_duplicate_pending_email_returns_409():
    student = _uf()
    client = _client_for(student)
    client.post(_create_url(), {"parent_email": "parent@example.test"}, format="json")

    response = client.post(_create_url(), {"parent_email": "parent@example.test"}, format="json")

    assert response.status_code == 409
    assert (
        ParentInvitation.objects.filter(student=student, parent_email="parent@example.test").count()
        == 1
    )


def test_create_invitation_second_different_email_is_not_blocked():
    student = _uf()
    client = _client_for(student)
    client.post(_create_url(), {"parent_email": "mother@example.test"}, format="json")

    response = client.post(_create_url(), {"parent_email": "father@example.test"}, format="json")

    assert response.status_code == 201
    assert ParentInvitation.objects.filter(student=student).count() == 2


def test_list_invitations_scoped_to_current_student():
    student = _uf()
    other = _uf()
    _client_for(other).post(_create_url(), {"parent_email": "x@example.test"}, format="json")
    _client_for(student).post(_create_url(), {"parent_email": "y@example.test"}, format="json")

    response = _client_for(student).get(_create_url())

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["parent_email"] == "y@example.test"


def test_resend_invitation_rate_limited_second_call_within_hour():
    student = _uf()
    client = _client_for(student)
    create_resp = client.post(_create_url(), {"parent_email": "p@example.test"}, format="json")
    invitation_id = create_resp.json()["id"]
    resend_url = reverse("family:parent-invitation-resend", kwargs={"invitation_id": invitation_id})

    first = client.post(resend_url)
    second = client.post(resend_url)

    assert first.status_code == 200, first.content
    assert second.status_code == 429


def test_non_student_cannot_create_invitation():
    parent = _uf(role="parent")
    client = _client_for(parent)

    response = client.post(_create_url(), {"parent_email": "x@example.test"}, format="json")

    assert response.status_code == 403
