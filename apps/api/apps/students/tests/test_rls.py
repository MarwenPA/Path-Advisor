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

import json
import uuid

import pytest
from django.db import connection, transaction

from apps.accounts.models import User, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.students.models import StudentProfile

pytestmark = [pytest.mark.postgresql_only, pytest.mark.rls]


def _set_gucs(cursor, *, user_id: str = "", tenant_id: str = "", actor_role: str = "") -> None:
    # Story 1.16: `set_config(..., is_local => true)` is TRANSACTION-scoped.
    # These tests run `django_db(transaction=True)` (autocommit), so a bare
    # `connection.cursor()` commits after every statement and the GUCs were
    # already '' by the time the next SELECT ran — several assertions here
    # were vacuously green/red for the wrong reason. Every act phase below
    # therefore wraps `_set_gucs` + query in `transaction.atomic()`, same as
    # `accounts/test_rls_isolation.py`. Do NOT call this outside atomic.
    if not connection.in_atomic_block:
        raise AssertionError(
            "_set_gucs uses transaction-local set_config; call it inside "
            "transaction.atomic() or the GUCs expire before the next statement "
            "(Story 1.16)."
        )
    cursor.execute(
        "SELECT "
        "set_config('app.current_user_id', %s, true), "
        "set_config('app.current_tenant_id', %s, true), "
        "set_config('app.actor_role', %s, true)",
        [user_id, tenant_id, actor_role],
    )


def _make_student(email: str, tenant_id: uuid.UUID | None = None) -> User:
    # Story 1.16: this lane runs as NOSUPERUSER NOBYPASSRLS under FORCE RLS,
    # so the arrange phase is itself subject to the policies — a bare
    # `User.objects.create` fails with "new row violates row-level security
    # policy". See `apps.core.rls_testing` for why this uses the policies'
    # existing `path_admin` branch rather than `bypass_rls()`.
    with as_path_admin():
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
    # Story 1.16: profile creation is still arrange — subject to
    # student_profiles_isolation_modify under FORCE RLS.
    with as_path_admin():
        StudentProfile.objects.create(user=alice, passions=["musique"])
        StudentProfile.objects.create(user=bob, passions=["cinema-series"])

    with transaction.atomic(), connection.cursor() as cursor:
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
    with as_path_admin():
        bob_profile = StudentProfile.objects.create(user=bob, passions=["cinema-series"])

    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        # Story 1.16: a bare Python list binds as a Postgres ARRAY, not jsonb
        # ("invalid input syntax for type json") — serialize explicitly so the
        # UPDATE is well-typed and rowcount 0 can only mean the RLS USING
        # clause filtered bob's row out.
        cursor.execute(
            "UPDATE student_profiles SET passions = %s::jsonb WHERE id = %s",
            [json.dumps(["TAMPERED"]), bob_profile.id],
        )
        affected = cursor.rowcount

    assert affected == 0

    # Story 1.16: `affected == 0` alone is vacuous — an empty-GUC session also
    # matches nothing. Prove the session was live by showing alice CAN reach
    # her own row under the exact same GUC recipe.
    with as_path_admin():
        alice_profile = StudentProfile.objects.create(user=alice, passions=["musique"])
    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        cursor.execute(
            "UPDATE student_profiles SET passions = %s::jsonb WHERE id = %s",
            [json.dumps(["jeux-video"]), alice_profile.id],
        )
        assert cursor.rowcount == 1, (
            "Control: alice must be able to UPDATE her own profile — otherwise "
            "the 0-rows result above proves nothing about isolation."
        )

    # Sanity — bob's row is untouched when we look at it as bob.
    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id=bob.id, actor_role="student")
        cursor.execute("SELECT passions FROM student_profiles WHERE id = %s", [bob_profile.id])
        row = cursor.fetchone()
    # Raw cursor returns jsonb as its text representation — parse before
    # comparing (this assertion had never actually run before Story 1.16).
    assert json.loads(row[0]) == ["cinema-series"]


@pytest.mark.django_db(transaction=True)
def test_student_cannot_insert_for_another_user(skip_if_sqlite):
    """Inserting a profile row with someone else's user_id must trip WITH CHECK."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")

    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        with pytest.raises(Exception) as exc_info:
            cursor.execute(
                # Story 1.16: `bulletins_status` added (Story 2.7 column,
                # NOT NULL) so a constraint violation can never masquerade
                # as the RLS rejection asserted below.
                "INSERT INTO student_profiles "
                "(id, user_id, tenant_id, passions, valeurs, interets, "
                " onboarding_step1_status, onboarding_step1_completed_at, "
                " bulletins_status, created_at, updated_at) "
                "VALUES (%s, %s, NULL, '[]'::jsonb, '[]'::jsonb, "
                ' \'{"1":null,"2":null,"3":null}\'::jsonb, '
                " 'pending', NULL, 'pending', now(), now())",
                ["sprf_test_bob_insert", bob.id],
            )
    # Postgres surfaces RLS WITH CHECK failures as "new row violates row-level security policy".
    assert (
        "row-level security" in str(exc_info.value).lower()
        or "policy" in str(exc_info.value).lower()
    )

    # Story 1.16 control: the same INSERT with alice's OWN user_id succeeds
    # under identical GUCs — proving the rejection above came from the
    # WITH CHECK user_id mismatch, not from an empty/dead session (which
    # rejects everything and made this test vacuously green before the
    # transaction-scoped `set_config` fix).
    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        cursor.execute(
            "INSERT INTO student_profiles "
            "(id, user_id, tenant_id, passions, valeurs, interets, "
            " onboarding_step1_status, onboarding_step1_completed_at, "
            " bulletins_status, created_at, updated_at) "
            "VALUES (%s, %s, NULL, '[]'::jsonb, '[]'::jsonb, "
            ' \'{"1":null,"2":null,"3":null}\'::jsonb, '
            " 'pending', NULL, 'pending', now(), now())",
            ["sprf_test_alice_insert", alice.id],
        )
        assert cursor.rowcount == 1


@pytest.mark.django_db(transaction=True)
def test_path_admin_sees_all_profiles(skip_if_sqlite):
    """path_admin actor_role bypasses the student-only USING clause."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")
    with as_path_admin():
        StudentProfile.objects.create(user=alice)
        StudentProfile.objects.create(user=bob)

    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id="admin-1", actor_role="path_admin")
        cursor.execute("SELECT count(*) FROM student_profiles")
        count = cursor.fetchone()[0]

    assert count == 2


@pytest.mark.django_db(transaction=True)
def test_anonymous_session_sees_nothing(skip_if_sqlite):
    """Unset GUCs → policy denies every row (deny by default).

    Story 1.16: before the transaction-scoped `set_config` fix this test was
    VACUOUS — the GUCs it "set" had already expired, so it observed empty
    GUCs no matter what and could never detect a broken deny-by-default
    branch being masked by a live session. The control SELECT below (alice
    sees her own row under the same recipe) proves the harness itself can
    produce a non-empty result, so `count == 0` is now meaningful.
    """
    alice = _make_student("alice@test.local")
    with as_path_admin():
        StudentProfile.objects.create(user=alice)

    # Control: the same harness with alice's GUCs sees exactly her row.
    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor, user_id=alice.id, actor_role="student")
        cursor.execute("SELECT count(*) FROM student_profiles")
        assert cursor.fetchone()[0] == 1

    with transaction.atomic(), connection.cursor() as cursor:
        _set_gucs(cursor)  # all empty
        cursor.execute("SELECT count(*) FROM student_profiles")
        count = cursor.fetchone()[0]

    assert count == 0


@pytest.mark.django_db(transaction=True)
def test_bypass_rls_opens_the_table(skip_if_sqlite):
    """`app.bypass_rls=true` is the system-task escape hatch (Story 1.8 D3)."""
    alice = _make_student("alice@test.local")
    bob = _make_student("bob@test.local")
    with as_path_admin():
        StudentProfile.objects.create(user=alice)
        StudentProfile.objects.create(user=bob)

    # Story 1.16: `set_config(..., true)` is transaction-local — under
    # autocommit it expired before the SELECT, so this asserted on an
    # anonymous session, not on the bypass branch. atomic() keeps it live.
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.bypass_rls', 'true', true)")
        cursor.execute("SELECT count(*) FROM student_profiles")
        count = cursor.fetchone()[0]

    assert count == 2
