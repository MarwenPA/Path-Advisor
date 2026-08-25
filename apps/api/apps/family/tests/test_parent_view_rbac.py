"""Story 6.2 — T6.2 / AC4 / AC5: authorization boundaries for the parent dashboard."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog
from apps.core.rls import bypass_rls
from apps.family.models import ParentStudentLink

pytestmark = pytest.mark.django_db


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _dashboard_url(student_id: str) -> str:
    return reverse("family:parent-child-dashboard", kwargs={"student_id": student_id})


def test_unauthenticated_is_refused():
    student = _uf()
    resp = APIClient().get(_dashboard_url(student.id))
    assert resp.status_code in (401, 403)


def test_non_parent_role_is_refused():
    student_actor = _uf()  # role=student
    target = _uf()
    client = APIClient()
    client.force_authenticate(user=student_actor)
    resp = client.get(_dashboard_url(target.id))
    assert resp.status_code == 403


def test_parent_not_linked_is_refused_and_audited():
    parent = _uf(role="parent")
    unrelated = _uf()

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_dashboard_url(unrelated.id))

    assert resp.status_code == 403
    body = resp.json()
    assert body["type"].endswith("parent-not-linked")
    with bypass_rls(reason="test_assert.read_audit"):
        assert AuditLog.objects.filter(
            action="parent.child_access_denied", subject_id=unrelated.id
        ).exists()


def test_parent_with_revoked_link_is_refused():
    from django.utils import timezone

    parent = _uf(role="parent")
    student = _uf()
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=student, revoked_at=timezone.now())

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_dashboard_url(student.id))

    assert resp.status_code == 403


def test_parent_linked_to_another_child_cannot_reach_this_one():
    parent = _uf(role="parent")
    linked = _uf()
    other = _uf()
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=linked)

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_dashboard_url(other.id))

    assert resp.status_code == 403
