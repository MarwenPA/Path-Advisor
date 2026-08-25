"""Story 6.1 — T8.4 / AC7: parent without an active link → refused.

No parent-facing data endpoint ships in this story (Story 6.2) — this test
exercises the `IsLinkedParent` building block directly, which is what any
future endpoint MUST compose to satisfy AC7 ("the non-revoked
`ParentStudentLink` is the SOLE source of authorization").
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.family.models import ParentStudentLink
from apps.family.permissions import IsLinkedParent

pytestmark = [pytest.mark.django_db, pytest.mark.postgresql_only]


def _uf(**kwargs):
    # `users` has FORCE RLS (Story 1.8) — test-setup writes go through the
    # sanctioned bypass helper (same pattern as apps/billing/tests/test_api.py).
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _request_for(user):
    request = Mock()
    request.user = user
    request.method = "GET"
    request.path = "/api/v1/students/me/profile"
    return request


def test_parent_without_any_link_is_refused():
    parent = _uf(role="parent")
    student = _uf()

    allowed = IsLinkedParent().has_object_permission(_request_for(parent), None, student)

    assert allowed is False


def test_parent_with_active_link_is_allowed():
    parent = _uf(role="parent")
    student = _uf()
    ParentStudentLink.objects.create(parent=parent, student=student)

    allowed = IsLinkedParent().has_object_permission(_request_for(parent), None, student)

    assert allowed is True


def test_parent_with_revoked_link_is_refused():
    from django.utils import timezone

    parent = _uf(role="parent")
    student = _uf()
    ParentStudentLink.objects.create(parent=parent, student=student, revoked_at=timezone.now())

    allowed = IsLinkedParent().has_object_permission(_request_for(parent), None, student)

    assert allowed is False


def test_student_role_is_never_granted_parent_access():
    other_student_acting_as_parent = _uf()  # role=student by default
    student = _uf()

    allowed = IsLinkedParent().has_object_permission(
        _request_for(other_student_acting_as_parent), None, student
    )

    assert allowed is False


def test_link_to_a_different_student_does_not_grant_access():
    parent = _uf(role="parent")
    linked_student = _uf()
    other_student = _uf()
    ParentStudentLink.objects.create(parent=parent, student=linked_student)

    allowed = IsLinkedParent().has_object_permission(_request_for(parent), None, other_student)

    assert allowed is False
