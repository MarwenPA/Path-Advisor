"""`TenantScopedModel.save()` behavior — Story 1.8 T1.

Uses a private test-only concrete subclass so we exercise the abstract base
without depending on any production feature model. Schema is created/dropped
in the same test transaction via `connection.schema_editor()`.
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection, models

from apps.core import request_context
from apps.core.models import TenantScopedModel


class _DummyScoped(TenantScopedModel):
    """Concrete subclass for tests only — never registered in production migrations."""

    label = models.CharField(max_length=20, default="")

    class Meta:
        app_label = "core"
        db_table = "_test_dummy_scoped"


@pytest.fixture(scope="module", autouse=True)
def _create_dummy_table(django_db_setup, django_db_blocker):
    """Create the test-only table once per module (outside per-test transactions).

    `schema_editor` cannot run inside SQLite's per-test transaction, so we
    materialise it at module scope. `django_db_setup` guarantees migrations
    have applied before we add our ephemeral table.
    """
    with django_db_blocker.unblock(), connection.schema_editor() as editor:
        editor.create_model(_DummyScoped)
    yield
    with django_db_blocker.unblock(), connection.schema_editor() as editor:
        editor.delete_model(_DummyScoped)


@pytest.mark.django_db
def test_save_with_actor_in_context_autofills_user_and_tenant():
    tenant = uuid.uuid4()

    class _FakeUser:
        is_authenticated = True
        id = "usr_01TEST"
        role = "student"
        tenant_id = tenant

    request_context.set_actor(_FakeUser())
    try:
        row = _DummyScoped(label="hello")
        row.save()
        row.refresh_from_db()
        assert row.user_id == "usr_01TEST"
        assert row.tenant_id == tenant
    finally:
        request_context.clear()


@pytest.mark.django_db
def test_save_with_b2c_actor_keeps_tenant_null():
    class _FakeUser:
        is_authenticated = True
        id = "usr_01B2C"
        role = "student"
        tenant_id = None

    request_context.set_actor(_FakeUser())
    try:
        row = _DummyScoped(label="hello")
        row.save()
        row.refresh_from_db()
        assert row.user_id == "usr_01B2C"
        assert row.tenant_id is None  # B2C user — RLS keys on user_id alone
    finally:
        request_context.clear()


@pytest.mark.django_db
def test_save_without_actor_raises_value_error():
    """Celery / shell / migration path: caller MUST supply user_id."""
    request_context.clear()
    row = _DummyScoped(label="orphan")
    with pytest.raises(ValueError, match="`user_id` is required"):
        row.save()


@pytest.mark.django_db
def test_save_with_explicit_user_id_overrides_context():
    """Explicit caller wins — useful for system tasks impersonating users."""

    class _FakeUser:
        is_authenticated = True
        id = "usr_01CTX"
        role = "student"
        tenant_id = uuid.uuid4()

    request_context.set_actor(_FakeUser())
    try:
        explicit_tenant = uuid.uuid4()
        row = _DummyScoped(
            label="explicit",
            user_id="usr_01EXPLICIT",
            tenant_id=explicit_tenant,
        )
        row.save()
        row.refresh_from_db()
        assert row.user_id == "usr_01EXPLICIT"
        assert row.tenant_id == explicit_tenant
    finally:
        request_context.clear()


@pytest.mark.django_db
def test_updated_at_changes_on_save():
    class _FakeUser:
        is_authenticated = True
        id = "usr_01UPD"
        role = "student"
        tenant_id = None

    request_context.set_actor(_FakeUser())
    try:
        row = _DummyScoped(label="initial")
        row.save()
        first_updated_at = row.updated_at
        row.label = "modified"
        row.save()
        row.refresh_from_db()
        assert row.updated_at > first_updated_at
    finally:
        request_context.clear()
