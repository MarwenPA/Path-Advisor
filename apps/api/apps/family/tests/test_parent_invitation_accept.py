"""Story 6.1 — T8.2: accept flow (AC3/AC4)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.family.models import ParentInvitationStatus, ParentStudentLink
from apps.family.services.parent_invitation import create_invitation

pytestmark = [pytest.mark.django_db, pytest.mark.postgresql_only]


def _uf(**kwargs):
    # `users` has FORCE RLS (Story 1.8) — test-setup writes go through the
    # sanctioned bypass helper (same pattern as apps/billing/tests/test_api.py).
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _status_url(token: str) -> str:
    return reverse("family:parent-invitation-status", kwargs={"token": token})


def _accept_url(token: str) -> str:
    return reverse("family:parent-invitation-accept", kwargs={"token": token})


def test_public_status_endpoint_returns_pending_state():
    student = _uf()
    invitation = create_invitation(student=student, parent_email="p@example.test")
    client = APIClient()

    response = client.get(_status_url(invitation.token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"


def test_public_status_endpoint_unknown_token_returns_404():
    client = APIClient()
    response = client.get(_status_url("does-not-exist"))
    assert response.status_code == 404


def test_accept_anonymous_creates_parent_user_and_link():
    student = _uf()
    invitation = create_invitation(
        student=student, parent_email="p@example.test", relationship="mere"
    )
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token),
        {"email": "p@example.test", "password": "Path-Advisor-2026!"},
        format="json",
    )

    assert response.status_code == 200, response.content
    # `users` has FORCE RLS — this bare test session has no `current_user_id`
    # GUC, so reading the freshly created parent row needs the bypass helper.
    with bypass_rls(reason="test_assert.read_parent_user"):
        parent = User.objects.get(email="p@example.test")
    assert parent.role == UserRole.PARENT
    link = ParentStudentLink.objects.get(parent=parent, student=student)
    assert link.revoked_at is None
    assert link.relationship == "mere"

    invitation.refresh_from_db()
    assert invitation.status == ParentInvitationStatus.ACCEPTED
    assert invitation.accepted_at is not None


def test_accept_auto_logs_in_new_parent():
    student = _uf()
    invitation = create_invitation(student=student, parent_email="p@example.test")
    client = APIClient()

    client.post(
        _accept_url(invitation.token),
        {"email": "p@example.test", "password": "Path-Advisor-2026!"},
        format="json",
    )

    # Session cookie was set by django_login — a subsequent authenticated call works.
    assert "sessionid" in client.cookies


def test_accept_email_already_registered_returns_409():
    student = _uf()
    _uf(email="taken@example.test")
    invitation = create_invitation(student=student, parent_email="taken@example.test")
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token),
        {"email": "taken@example.test", "password": "Path-Advisor-2026!"},
        format="json",
    )

    assert response.status_code == 409


def test_accept_expired_or_invalid_token_returns_404():
    client = APIClient()
    response = client.post(
        _accept_url("not-a-real-token"),
        {"email": "x@example.test", "password": "Path-Advisor-2026!"},
        format="json",
    )
    assert response.status_code == 404


def test_accept_by_already_authenticated_parent_adds_second_link_no_new_account():
    student_a = _uf()
    student_b = _uf()
    parent_email = "shared-parent@example.test"

    invitation_a = create_invitation(student=student_a, parent_email=parent_email)
    client = APIClient()
    client.post(
        _accept_url(invitation_a.token),
        {"email": parent_email, "password": "irrelevant-strong-pw"},
        format="json",
    )
    # First acceptance creates the account for `parent_email` — fetch it under
    # the RLS bypass (FORCE RLS on `users`, bare test session has no GUC).
    with bypass_rls(reason="test_assert.read_parent_user"):
        real_parent = User.objects.get(email=parent_email)

    invitation_b = create_invitation(student=student_b, parent_email=real_parent.email)
    client_authed = APIClient()
    client_authed.force_authenticate(user=real_parent)
    response = client_authed.post(
        _accept_url(invitation_b.token),
        {},
        format="json",
    )

    assert response.status_code == 200, response.content
    with bypass_rls(reason="test_assert.read_parent_user"):
        assert User.objects.filter(email=real_parent.email).count() == 1
    assert ParentStudentLink.objects.filter(parent=real_parent).count() == 2
