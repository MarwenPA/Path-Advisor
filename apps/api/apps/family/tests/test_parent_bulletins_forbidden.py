"""Story 6.2 — T6.3 / AC3: a parent may NEVER read a child's bulletins (403 + audit)."""

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


def _bulletins_url(student_id: str) -> str:
    return reverse("family:parent-child-bulletins", kwargs={"student_id": student_id})


def test_linked_parent_still_forbidden_on_bulletins_and_audited():
    parent = _uf(role="parent")
    student = _uf()
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=student)

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_bulletins_url(student.id))

    assert resp.status_code == 403
    body = resp.json()
    assert body["type"].endswith("parent-bulletins-forbidden")
    with bypass_rls(reason="test_assert.read_audit"):
        assert AuditLog.objects.filter(
            action="parent.bulletins_access_denied", subject_id=student.id
        ).exists()


def test_student_role_refused_on_parent_bulletins_endpoint():
    actor = _uf()  # role=student
    target = _uf()
    client = APIClient()
    client.force_authenticate(user=actor)
    resp = client.get(_bulletins_url(target.id))
    assert resp.status_code == 403
