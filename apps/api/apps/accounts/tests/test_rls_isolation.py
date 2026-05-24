"""Story 1.8 — End-to-end RLS isolation tests.

These tests REQUIRE a real PostgreSQL backend AND a non-superuser DB role —
SQLite has no Row-Level Security, and PostgreSQL silently bypasses FORCE
ROW LEVEL SECURITY for superusers and table owners with the `BYPASSRLS`
attribute. Marked `postgresql_only` + `rls`; runs under `make test-rls`.

Each test sets the three session GUCs the policies key on
(`app.current_user_id`, `app.current_tenant_id`, `app.actor_role`) using
`SET LOCAL` so the values vanish on transaction commit / rollback — same
contract as `TenantSessionMiddleware`.

Coverage matrix:

| AC  | Test                                                          | Scenario                                              |
|-----|---------------------------------------------------------------|-------------------------------------------------------|
| AC4 | test_users_select_cross_tenant_blocked                        | tenant A cannot read tenant B's user row              |
| AC4 | test_users_select_path_admin_bypasses_rls                     | path_admin sees both tenants                          |
| AC5 | test_parental_consents_select_cross_user_blocked              | same tenant, different student → denied               |
| AC5 | test_parental_consents_insert_respects_user                   | inserting for someone else is rejected                |
| AC6 | test_raw_sql_injection_pattern_still_filtered                 | `SELECT * WHERE 1=1` still scoped at engine layer     |
| —   | test_anonymous_session_sees_nothing                           | unset GUCs → empty result (deny by default)           |
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection, transaction

from apps.accounts.models import ParentalConsent, User, UserRole, UserStatus

pytestmark = [pytest.mark.postgresql_only, pytest.mark.rls]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_gucs(cursor, *, user_id: str = "", tenant_id: str = "", actor_role: str = "") -> None:
    """Mirror `TenantSessionMiddleware` GUC writes inside a test transaction."""
    cursor.execute(
        "SELECT "
        "set_config('app.current_user_id', %s, true), "
        "set_config('app.current_tenant_id', %s, true), "
        "set_config('app.actor_role', %s, true)",
        [user_id, tenant_id, actor_role],
    )


def _make_user(
    *,
    email: str,
    tenant_id: uuid.UUID | None,
    role: str = UserRole.STUDENT,
    status: str = UserStatus.ACTIVE,
) -> User:
    """Create a User row directly via the ORM (test setup runs as table owner)."""
    user = User.objects.create(
        email=email,
        tenant_id=tenant_id,
        role=role,
        status=status,
        email_verified_at=None,
    )
    user.set_password("Path-Advisor-2026!")
    user.save()
    return user


# ---------------------------------------------------------------------------
# AC4 — Cross-tenant isolation on `users`
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_users_select_cross_tenant_blocked(skip_if_sqlite):
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user_a = _make_user(email="a@example.test", tenant_id=tenant_a)
    user_b = _make_user(email="b@example.test", tenant_id=tenant_b)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id=user_a.id,
            tenant_id=str(tenant_a),
            actor_role=UserRole.STUDENT,
        )
        cur.execute("SELECT id FROM users ORDER BY id")
        visible_ids = {row[0] for row in cur.fetchall()}

    assert user_a.id in visible_ids
    assert user_b.id not in visible_ids, (
        "RLS users_isolation_select must hide cross-tenant users."
    )


@pytest.mark.django_db(transaction=True)
def test_users_select_path_admin_bypasses_rls(skip_if_sqlite):
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user_a = _make_user(email="a-admin@example.test", tenant_id=tenant_a)
    user_b = _make_user(email="b-admin@example.test", tenant_id=tenant_b)
    admin = _make_user(
        email="dpo@example.test",
        tenant_id=None,
        role=UserRole.PATH_ADMIN,
    )

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id=admin.id,
            tenant_id="",
            actor_role=UserRole.PATH_ADMIN,
        )
        cur.execute("SELECT id FROM users")
        visible_ids = {row[0] for row in cur.fetchall()}

    assert {user_a.id, user_b.id, admin.id}.issubset(visible_ids), (
        "path_admin must see every tenant's rows (back-office requirement)."
    )


@pytest.mark.django_db(transaction=True)
def test_users_select_same_tenant_counselor_sees_cohort(skip_if_sqlite):
    """Counselor in tenant T1 sees other students in T1 — Epic 6 prerequisite."""
    tenant = uuid.uuid4()
    counselor = _make_user(email="c@example.test", tenant_id=tenant, role=UserRole.COUNSELOR)
    student = _make_user(email="s@example.test", tenant_id=tenant, role=UserRole.STUDENT)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id=counselor.id,
            tenant_id=str(tenant),
            actor_role=UserRole.COUNSELOR,
        )
        cur.execute("SELECT id FROM users WHERE tenant_id = %s", [str(tenant)])
        visible_ids = {row[0] for row in cur.fetchall()}

    assert visible_ids == {counselor.id, student.id}


@pytest.mark.django_db(transaction=True)
def test_anonymous_session_sees_nothing(skip_if_sqlite):
    """Unset GUCs → all `current_setting` values empty → every row denied."""
    _make_user(email="lonely@example.test", tenant_id=uuid.uuid4())

    with transaction.atomic(), connection.cursor() as cur:
        # Explicitly clear all GUCs (mirrors anonymous request branch of
        # TenantSessionMiddleware).
        _set_gucs(cur)
        cur.execute("SELECT id FROM users")
        rows = cur.fetchall()

    assert rows == [], "Anonymous session must not read user data."


# ---------------------------------------------------------------------------
# AC5 — Cross-user isolation on `parental_consents` (stricter than users)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_parental_consents_select_cross_user_blocked(skip_if_sqlite):
    """Two students same tenant — student A must not see student B's consent."""
    tenant = uuid.uuid4()
    student_a = _make_user(email="sa@example.test", tenant_id=tenant)
    student_b = _make_user(email="sb@example.test", tenant_id=tenant)
    consent_a = ParentalConsent.objects.create(
        student=student_a,
        parent_email="pa@example.test",
        token=f"tok-{uuid.uuid4().hex}",
    )
    consent_b = ParentalConsent.objects.create(
        student=student_b,
        parent_email="pb@example.test",
        token=f"tok-{uuid.uuid4().hex}",
    )

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id=student_a.id,
            tenant_id=str(tenant),
            actor_role=UserRole.STUDENT,
        )
        cur.execute("SELECT id FROM parental_consents ORDER BY id")
        visible_ids = {row[0] for row in cur.fetchall()}

    assert consent_a.id in visible_ids
    assert consent_b.id not in visible_ids, (
        "RLS parental_consents_isolation_select must block cross-user reads "
        "even within the same tenant."
    )


@pytest.mark.django_db(transaction=True)
def test_parental_consents_insert_respects_user(skip_if_sqlite):
    """Inserting a consent for someone else's student_id must be rejected by the policy."""
    tenant = uuid.uuid4()
    student_a = _make_user(email="ia@example.test", tenant_id=tenant)
    student_b = _make_user(email="ib@example.test", tenant_id=tenant)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id=student_a.id,
            tenant_id=str(tenant),
            actor_role=UserRole.STUDENT,
        )
        with pytest.raises(Exception) as exc_info:
            cur.execute(
                "INSERT INTO parental_consents (id, student_id, parent_email, token, "
                "requested_at, expires_at, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, NOW(), NOW() + INTERVAL '60 days', NOW(), NOW())",
                [
                    f"pcn_test_{uuid.uuid4().hex[:8]}",
                    student_b.id,  # impersonation attempt!
                    "evil@example.test",
                    f"evil-{uuid.uuid4().hex}",
                ],
            )
        # The exception is a `psycopg.errors.RaiseException` or similar — its
        # message includes "row-level security policy" verbatim.
        assert "row-level security" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# AC6 — Raw SQL bypass attempt
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_raw_sql_injection_pattern_still_filtered(skip_if_sqlite):
    """`SELECT * FROM users WHERE 1=1` via a raw cursor — RLS still applies.

    Documents what RLS protects against: engine-level enforcement. The leak
    a missing `.filter(tenant_id=...)` would produce is structurally
    impossible because the policy filter runs regardless of WHERE clauses.
    """
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user_a = _make_user(email="ra@example.test", tenant_id=tenant_a)
    user_b = _make_user(email="rb@example.test", tenant_id=tenant_b)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id=user_a.id,
            tenant_id=str(tenant_a),
            actor_role=UserRole.STUDENT,
        )
        # Mimic a SQL injection that bypassed all ORM filters: `WHERE 1=1`.
        cur.execute("SELECT id FROM users WHERE 1=1")
        rows = {row[0] for row in cur.fetchall()}

    assert user_a.id in rows
    assert user_b.id not in rows, (
        "Even a `WHERE 1=1` bypass must not leak cross-tenant data — RLS "
        "applies at the engine layer."
    )
