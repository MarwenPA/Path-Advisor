"""AuditLog model tests — ID format, hash chain, immutability via ORM."""

from __future__ import annotations

import re

import pytest
from django.db import connection
from django.utils import timezone

from apps.audit.decorators import record_audit
from apps.audit.models import AuditLog, AuditResult
from apps.audit.tests.factories import AuditLogFactory
from apps.core.exceptions import AuditLogImmutable

ULID_ID_RE = re.compile(r"^aud_[0-9A-HJKMNP-TV-Z]{26}$")


@pytest.mark.django_db
def test_audit_log_create_writes_row_with_prefixed_ulid_id():
    row = record_audit(action="test.event", result=AuditResult.SUCCESS, metadata={"k": "v"})
    assert row is not None
    assert ULID_ID_RE.match(row.id), f"Unexpected id: {row.id}"


@pytest.mark.django_db
def test_audit_log_hash_chain_first_row_has_empty_prev_hash():
    row = record_audit(action="test.first", result=AuditResult.SUCCESS)
    assert row is not None
    assert row.prev_hash in (None, "")
    assert row.row_hash  # non-empty


@pytest.mark.django_db
def test_audit_log_hash_chain_links_to_previous_row():
    first = record_audit(action="test.first", result=AuditResult.SUCCESS)
    second = record_audit(action="test.second", result=AuditResult.SUCCESS)
    assert first is not None and second is not None
    assert second.prev_hash == first.row_hash
    assert second.row_hash != first.row_hash


@pytest.mark.django_db
def test_audit_log_update_via_manager_raises_immutable_error():
    AuditLogFactory.create(action="x.y")
    with pytest.raises(AuditLogImmutable):
        AuditLog.objects.filter(action="x.y").update(action="hacked")


@pytest.mark.django_db
def test_audit_log_delete_via_manager_raises_immutable_error():
    AuditLogFactory.create(action="x.z")
    with pytest.raises(AuditLogImmutable):
        AuditLog.objects.filter(action="x.z").delete()


@pytest.mark.django_db
def test_audit_log_save_on_existing_pk_raises_immutable_error():
    row = AuditLogFactory.create()
    row.action = "tampered"
    with pytest.raises(AuditLogImmutable):
        row.save()


@pytest.mark.django_db
def test_audit_log_metadata_stable_across_repr():
    """Hash must be deterministic regardless of dict insertion order."""
    first = record_audit(
        action="test.deterministic", result=AuditResult.SUCCESS, metadata={"b": 2, "a": 1}
    )
    assert first is not None
    # Recreate the same payload from the row and recompute the hash manually.
    from apps.audit.services.hash_chain import compute_row_hash

    expected = compute_row_hash(
        actor_id=first.actor_id,
        action=first.action,
        subject_id=first.subject_id,
        metadata=first.metadata,
        created_at=first.created_at,
        prev_hash=first.prev_hash,
    )
    assert expected == first.row_hash


@pytest.mark.postgresql_only
@pytest.mark.django_db
def test_audit_log_update_blocked_at_db_level(skip_if_sqlite):
    """The PostgreSQL trigger refuses UPDATE even when bypassing the ORM."""
    AuditLogFactory.create(action="trigger.test")
    with pytest.raises(Exception) as excinfo, connection.cursor() as cur:
        cur.execute("UPDATE audit_logs SET action = 'tampered' WHERE action = 'trigger.test'")
    assert "audit_logs" in str(excinfo.value).lower()


@pytest.mark.django_db
def test_audit_log_str_includes_action_and_actor():
    row = AuditLogFactory.create(action="display.test", actor_id="usr_x", created_at=timezone.now())
    assert "display.test" in str(row)
    assert "usr_x" in str(row)
