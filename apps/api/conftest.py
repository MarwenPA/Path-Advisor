"""Project-wide pytest fixtures.

Anything cross-cutting that test files in any app would otherwise duplicate
lives here. App-specific helpers stay in their own `apps/<app>/tests/conftest.py`.
"""

from __future__ import annotations

import pytest
from django.db import connection

from apps.core import request_context


@pytest.fixture(autouse=True)
def _audit_request_context_isolation():
    """Reset the audit thread-local + Postgres session GUCs around every test.

    Two stores carry per-request context across the codebase:
    1. `apps.core.request_context` thread-local — read by the audit decorator.
    2. Postgres session GUCs (`app.current_user_id`, `app.current_tenant_id`,
       `app.actor_role`) — read by the RLS policies (Story 1.8).

    Without this fixture, leaked state from a previous test (especially
    under pytest-xdist worker thread reuse or connection pooling) would
    taint subsequent audit rows OR mask RLS bugs by letting a previous
    test's GUCs satisfy the next test's policy check.
    """
    request_context.clear()
    if connection.vendor == "postgresql":
        # `RESET ALL` clears every SET in the current session, including
        # custom `app.*` GUCs the middleware writes. Cheap operation.
        with connection.cursor() as cursor:
            cursor.execute("RESET ALL")
    yield
    request_context.clear()
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("RESET ALL")


@pytest.fixture
def skip_if_sqlite(db):
    """Mark dependent tests as PostgreSQL-only and skip on SQLite.

    Promoted from `apps/audit/tests/conftest.py` to project scope (Story 1.8
    T7) — the RLS isolation suite uses the same gate, so duplicating it
    invited drift. Audit tests still import this fixture by the same name.
    """
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL (RLS policies / append-only trigger).")


@pytest.fixture(scope="session", autouse=True)
def _assert_non_superuser_in_postgres_lane(django_db_setup, django_db_blocker):
    """Hard-fail the suite if the PG test role is a superuser.

    `FORCE ROW LEVEL SECURITY` is silently bypassed for superusers (and roles
    with `BYPASSRLS`). A green RLS test under a superuser is a false positive
    — the policy is never exercised. This fixture turns that into a
    suite-startup failure (Story 1.8 §T7 §6 #1 mitigation).

    No-op on SQLite (no concept of superuser).
    """
    if connection.vendor != "postgresql":
        return
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("SHOW is_superuser")
        is_super = (cursor.fetchone() or [""])[0]
        cursor.execute(
            "SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )
        bypass = (cursor.fetchone() or [False])[0]
    if str(is_super).lower() == "on" or bypass:
        pytest.exit(
            "RLS guard: the test DB role is a superuser or has BYPASSRLS — "
            "`FORCE ROW LEVEL SECURITY` will be silently bypassed. Provision "
            "the CI role with `NOSUPERUSER NOBYPASSRLS` (see Story 1.8 T7).",
            returncode=2,
        )
