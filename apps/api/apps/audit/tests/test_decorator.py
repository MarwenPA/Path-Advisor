"""Tests for the `@audit_action` decorator and the `record_audit` helper."""

from __future__ import annotations

import pytest

from apps.audit.decorators import audit_action, record_audit
from apps.audit.models import AuditLog, AuditResult
from apps.core import request_context


@pytest.mark.django_db
def test_audit_action_decorator_creates_log_on_success():
    @audit_action(
        "test.decorated",
        subject_from=lambda kwargs, ret: ret,
        metadata_from=lambda kwargs, ret: {"x": kwargs.get("x")},
    )
    def fn(*, x: int) -> str:
        return f"subject_{x}"

    fn(x=42)

    rows = list(AuditLog.objects.filter(action="test.decorated"))
    assert len(rows) == 1
    assert rows[0].result == AuditResult.SUCCESS
    assert rows[0].subject_id == "subject_42"
    assert rows[0].metadata == {"x": 42}


@pytest.mark.django_db
def test_audit_action_decorator_creates_failure_log_on_exception_and_reraises():
    @audit_action("test.failure")
    def fn() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        fn()

    rows = list(AuditLog.objects.filter(action="test.failure"))
    assert len(rows) == 1
    assert rows[0].result == AuditResult.FAILURE
    assert rows[0].metadata == {"error_type": "ValueError"}


@pytest.mark.django_db
def test_audit_action_decorator_extracts_subject_id_from_string_kwarg():
    @audit_action("test.subject_from_str", subject_from="target_id")
    def fn(*, target_id: str) -> None:
        return None

    fn(target_id="usr_target_01")

    row = AuditLog.objects.get(action="test.subject_from_str")
    assert row.subject_id == "usr_target_01"


@pytest.mark.django_db
def test_audit_action_decorator_extracts_metadata_from_callable():
    @audit_action(
        "test.metadata",
        metadata_from=lambda kwargs, ret: {"input": kwargs["payload"], "output": ret},
    )
    def fn(*, payload: dict) -> str:
        return "ok"

    fn(payload={"a": 1})
    row = AuditLog.objects.get(action="test.metadata")
    assert row.metadata == {"input": {"a": 1}, "output": "ok"}


@pytest.mark.django_db
def test_record_audit_uses_request_context_for_actor():
    class _FakeUser:
        is_authenticated = True
        id = "usr_ctx_01"
        role = "path_admin"
        tenant_id = None

    request_context.set_actor(_FakeUser())
    record_audit(action="test.actor_from_context", result=AuditResult.SUCCESS)

    row = AuditLog.objects.get(action="test.actor_from_context")
    assert row.actor_id == "usr_ctx_01"
    assert row.actor_role == "path_admin"


@pytest.mark.django_db
def test_record_audit_with_actor_override_takes_priority():
    class _Actor:
        id = "usr_override"
        role = "student"

    record_audit(action="test.actor_override", result=AuditResult.SUCCESS, actor=_Actor())
    row = AuditLog.objects.get(action="test.actor_override")
    assert row.actor_id == "usr_override"
    assert row.actor_role == "student"
