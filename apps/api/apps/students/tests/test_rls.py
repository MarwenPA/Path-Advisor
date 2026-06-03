"""Story 2.1 — RLS isolation tests for `student_profiles`.

Mirror the Story 1.8 / `accounts.test_rls_isolation` pattern. PostgreSQL
only — runs under `make test-rls`. SQLite has no RLS engine, so the
suite is marked `postgresql_only` and `rls`.

Coverage matrix:

| Scenario                                                                 |
|--------------------------------------------------------------------------|
| Student A cannot SELECT student B's profile                              |
| Student A cannot UPDATE student B's profile (WITH CHECK rejects)         |
| path_admin sees both students' profiles                                  |
| Anonymous session (unset GUCs) sees nothing — deny by default            |
| Bypass GUC opens the table for system tasks                              |
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection

from apps.accounts.models import User, UserStatus
from apps.students.models import StudentProfile

pytestmark = [pytest.mark.postgresql_only, pytest.mark.rls]


def _set_gucs(cursor, *, user_id: str = "", tenant_id: str = "", actor_role: str = "") -> None:
    cursor.execute(
        "SELECT "
        "set_config('app.current_user_id', %s, true), "
        "set_config('app.current_tenant_id', %s, true), "
        "set_config('app.actor_role', %s, true)",
        [user_id, tenant_id, actor_role],
    )


def _make_student(email: str, tenant_id: uuid.UUID | None = None) -> User:
    user = User.objects.create(
        email=email,
        tenant_id=tenant_id,
        status=UserStatus.ACTIVE,
        email_verified_at=None,
    )
    user.set_password("Path-Advisor-2026!")
    user.save()
    return user


@pytest.mark.django_db(transaction=True)
def test_student_cannot_select_other_student_profile(skip_if_sqlite):
    """Student A's session must not SELECT Student B's profile."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")
    StudentProfile.objects.create(user=alice, passions=["musique"])
    StudentProfile.objects.create(user=bob, passions=["cinema-series"])

    with connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        cursor.execute("SELECT user_id, passions FROM student_profiles")
        rows = cursor.fetchall()

    assert len(rows) == 1
    assert rows[0][0] == alice.id


@pytest.mark.django_db(transaction=True)
def test_student_cannot_update_other_student_profile(skip_if_sqlite):
    """UPDATE under Student A's session must affect 0 rows for Student B's profile.

    RLS USING clause filters the row out — the UPDATE silently matches nothing.
    """
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")
    bob_profile = StudentProfile.objects.create(user=bob, passions=["cinema-series"])

    with connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        cursor.execute(
            "UPDATE student_profiles SET passions = %s WHERE id = %s",
            [["TAMPERED"], bob_profile.id],
        )
        affected = cursor.rowcount

    assert affected == 0

    # Sanity — bob's row is untouched when we look at it as bob.
    with connection.cursor() as cursor:
        _set_gucs(cursor, user_id=bob.id, actor_role="student")
        cursor.execute("SELECT passions FROM student_profiles WHERE id = %s", [bob_profile.id])
        row = cursor.fetchone()
    assert row[0] == ["cinema-series"]


@pytest.mark.django_db(transaction=True)
def test_student_cannot_insert_for_another_user(skip_if_sqlite):
    """Inserting a profile row with someone else's user_id must trip WITH CHECK."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")

    with connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        with pytest.raises(Exception) as exc_info:
            cursor.execute(
                "INSERT INTO student_profiles "
                "(id, user_id, tenant_id, passions, valeurs, interets, "
                " onboarding_step1_status, onboarding_step1_completed_at, "
                " created_at, updated_at) "
                "VALUES (%s, %s, NULL, '[]'::jsonb, '[]'::jsonb, "
                " '{\"1\":null,\"2\":null,\"3\":null}'::jsonb, "
                " 'pending', NULL, now(), now())",
                ["sprf_test_bob_insert", bob.id],
            )
    # Postgres surfaces RLS WITH CHECK failures as "new row violates row-level security policy".
    assert "row-level security" in str(exc_info.value).lower() or "policy" in str(exc_info.value).lower()


@pytest.mark.django_db(transaction=True)
def test_path_admin_sees_all_profiles(skip_if_sqlite):
    """path_admin actor_role bypasses the student-only USING clause."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")
    StudentProfile.objects.create(user=alice)
    StudentProfile.objects.create(user=bob)

    with connection.cursor() as cursor:
        _set_gucs(cursor, user_id="admin-1", actor_role="path_admin")
        cursor.execute("SELECT count(*) FROM student_profiles")
        count = cursor.fetchone()[0]

    assert count == 2


@pytest.mark.django_db(transaction=True)
def test_anonymous_session_sees_nothing(skip_if_sqlite):
    """Unset GUCs → policy denies every row (deny by default)."""
    alice = _make_student("alice@test.local")
    StudentProfile.objects.create(user=alice)

    with connection.cursor() as cursor:
        _set_gucs(cursor)  # all empty
        cursor.execute("SELECT count(*) FROM student_profiles")
        count = cursor.fetchone()[0]

    assert count == 0


@pytest.mark.django_db(transaction=True)
def test_bypass_rls_opens_the_table(skip_if_sqlite):
    """`app.bypass_rls=true` is the system-task escape hatch (Story 1.8 D3)."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")
    StudentProfile.objects.create(user=alice)
    StudentProfile.objects.create(user=bob)

    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.bypass_rls', 'true', true)")
        cursor.execute("SELECT count(*) FROM student_profiles")
        count = cursor.fetchone()[0]

    assert count == 2
