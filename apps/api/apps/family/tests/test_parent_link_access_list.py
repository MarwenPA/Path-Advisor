"""Story 6.1 — T8.3: ParentLinkSource in the AccessListAggregator, revoke, ownership."""

from __future__ import annotations

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog
from apps.core.rls import bypass_rls
from apps.family.access_list.parent_link import ParentLinkSource
from apps.family.models import ParentStudentLink
from apps.profiles.access_list import AccessListAggregator, registry
from apps.profiles.access_list.exceptions import EntryNotFound
from apps.profiles.access_list.results import RevocationResult

pytestmark = [pytest.mark.django_db, pytest.mark.postgresql_only]


def _uf(**kwargs):
    # `users` has FORCE RLS (Story 1.8) — test-setup writes go through the
    # sanctioned bypass helper (same pattern as apps/billing/tests/test_api.py).
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _link(student, parent, **kwargs):
    return ParentStudentLink.objects.create(student=student, parent=parent, **kwargs)


def test_parent_link_source_registered_in_live_registry():
    assert registry.get_source_by_name("parent_link") is not None


def test_list_for_user_returns_active_links_only():
    student = _uf()
    parent = _uf(role="parent")
    active = _link(student, parent)
    revoked_parent = _uf(role="parent")
    from django.utils import timezone

    _link(student, revoked_parent, revoked_at=timezone.now())

    entries = ParentLinkSource().list_for_user(student)

    assert len(entries) == 1
    assert entries[0].id == f"parent_link:{active.id}"
    assert entries[0].tier_type == "parent"
    assert entries[0].display_name == parent.email


def test_aggregator_includes_parent_link_source():
    student = _uf()
    parent = _uf(role="parent")
    _link(student, parent)

    agg = AccessListAggregator()
    entries = agg.list_for_user(student)

    assert any(e.source_name == "parent_link" for e in entries)


def test_revoke_stamps_revoked_at_and_writes_audit_row():
    student = _uf()
    parent = _uf(role="parent")
    link = _link(student, parent)

    result = ParentLinkSource().revoke(student, str(link.id))

    assert result == RevocationResult.PERFORMED
    link.refresh_from_db()
    assert link.revoked_at is not None


def test_revoke_is_idempotent_on_second_call():
    student = _uf()
    parent = _uf(role="parent")
    link = _link(student, parent)

    ParentLinkSource().revoke(student, str(link.id))
    result = ParentLinkSource().revoke(student, str(link.id))

    assert result == RevocationResult.ALREADY_REVOKED


def test_revoke_blocks_cross_student_ownership():
    student = _uf()
    other_student = _uf()
    parent = _uf(role="parent")
    link = _link(student, parent)

    with pytest.raises(EntryNotFound):
        ParentLinkSource().revoke(other_student, str(link.id))


def test_revoke_entry_via_generic_revoker_writes_profile_access_revoked_audit():
    from apps.profiles.access_list.revoker import revoke_entry

    student = _uf()
    parent = _uf(role="parent")
    link = _link(student, parent)

    revoke_entry(student, f"parent_link:{link.id}")

    assert AuditLog.objects.filter(action="profile.access_revoked").exists()
