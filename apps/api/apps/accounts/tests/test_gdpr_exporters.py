"""Story 1.11 — exporter registry + bundled accounts/audit exporters."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from apps.accounts.exporters import (
    ExporterEntry,
    iter_exporters,
    register_exporter,
)
from apps.accounts.exporters.accounts import export_account_profile
from apps.accounts.exporters.audit import export_audit_log
from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog, AuditResult

_T0 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_registry_iteration_is_alphabetical():
    domains = [name for name, _ in iter_exporters()]
    assert domains == sorted(domains), (
        "iter_exporters must yield domains in stable alphabetical order for "
        "byte-reproducible archives."
    )


def test_register_duplicate_raises():
    def fake(_user):
        return []

    with pytest.raises(ValueError, match="already registered"):
        register_exporter("accounts")(fake)


@pytest.mark.django_db
def test_account_exporter_emits_one_profile_json():
    user = UserFactory(email="sarah@example.test")
    entries = list(export_account_profile(user))
    assert len(entries) == 1
    entry = entries[0]
    assert isinstance(entry, ExporterEntry)
    assert entry.archive_path == "profile/profile.json"
    assert entry.content_type == "application/json"
    data = json.loads(entry.content)
    assert data["id"] == user.id
    assert data["email"] == "sarah@example.test"
    assert data["role"] == user.role
    assert "consent_rgpd_at" in data


@pytest.mark.django_db
def test_audit_exporter_filters_by_subject_or_actor():
    user_a = UserFactory()
    user_b = UserFactory()

    # user_a is subject
    AuditLog.objects.create(
        action="user.signed_up",
        result=AuditResult.SUCCESS,
        subject_id=user_a.id,
        actor_id=user_a.id,
        actor_role=user_a.role,
        row_hash="a" * 64,
        created_at=_T0,
    )
    # user_b only — not in user_a's export
    AuditLog.objects.create(
        action="user.signed_up",
        result=AuditResult.SUCCESS,
        subject_id=user_b.id,
        actor_id=user_b.id,
        actor_role=user_b.role,
        row_hash="b" * 64,
        created_at=_T0 + timedelta(seconds=60),
    )
    # user_a as actor on user_b — also goes into user_a's export
    AuditLog.objects.create(
        action="consent.granted",
        result=AuditResult.SUCCESS,
        subject_id=user_b.id,
        actor_id=user_a.id,
        actor_role=user_a.role,
        row_hash="c" * 64,
        created_at=_T0 + timedelta(seconds=120),
    )

    entries = list(export_audit_log(user_a))
    assert len(entries) == 1
    content = entries[0].content.decode("utf-8")
    lines = [json.loads(line) for line in content.strip().split("\n")]
    actions = [event["action"] for event in lines]
    assert actions == ["user.signed_up", "consent.granted"], (
        "audit exporter must include rows where the user is subject OR actor, in chronological order."
    )
    # Hash chain fields are internal — must NOT leak into the user-facing export.
    for event in lines:
        assert "row_hash" not in event
        assert "prev_hash" not in event


@pytest.mark.django_db
def test_audit_exporter_empty_for_user_without_events():
    user_without_audit = UserFactory()
    # Other users may have rows in `audit_logs` (signup signal etc.) — the
    # exporter must only see this user's. AuditLog is append-only at the ORM
    # level so we can't clear it; we rely on the filter being correct.
    entries = list(export_audit_log(user_without_audit))
    assert entries == []
