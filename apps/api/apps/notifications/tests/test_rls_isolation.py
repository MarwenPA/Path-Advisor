"""Story 8.2 — RLS isolation for `notification_preferences`.

PostgreSQL only (mirrors the 1.16 conventions exactly: arrange under
`as_path_admin`, act inside `transaction.atomic()` with all three GUCs set
locally, positive controls so a `count == 0` can never be vacuous).
"""

from __future__ import annotations

import pytest
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.notifications.models import NotificationCategory, NotificationPreference

pytestmark = [pytest.mark.postgresql_only, pytest.mark.rls]

CAT = NotificationCategory.SCHOOL_RESPONSES.value


def _set_gucs(cursor, *, user_id: str = "", actor_role: str = "") -> None:
    if not connection.in_atomic_block:
        raise AssertionError(
            "_set_gucs uses transaction-local set_config; call inside atomic() (Story 1.16)."
        )
    cursor.execute(
        "SELECT set_config('app.current_user_id', %s, true), "
        "set_config('app.current_tenant_id', '', true), "
        "set_config('app.actor_role', %s, true)",
        [user_id, actor_role],
    )


def _make_student(email: str) -> User:
    with as_path_admin():
        return User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )


@pytest.mark.django_db(transaction=True)
def test_cross_user_preferences_are_invisible(skip_if_sqlite):
    alice = _make_student("alice-notif@test.local")
    bob = _make_student("bob-notif@test.local")
    with as_path_admin():
        NotificationPreference.objects.create(user=alice, category=CAT, enabled=False)
        NotificationPreference.objects.create(user=bob, category=CAT, enabled=False)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur, user_id=alice.id, actor_role="student")
        cur.execute("SELECT user_id FROM notification_preferences")
        visible = {r[0] for r in cur.fetchall()}

    assert alice.id in visible  # positive control — the session is live
    assert bob.id not in visible, "RLS must hide other users' notification preferences."


@pytest.mark.django_db(transaction=True)
def test_cross_user_update_matches_nothing(skip_if_sqlite):
    alice = _make_student("alice-notif@test.local")
    bob = _make_student("bob-notif@test.local")
    with as_path_admin():
        bob_pref = NotificationPreference.objects.create(user=bob, category=CAT, enabled=True)
        alice_pref = NotificationPreference.objects.create(user=alice, category=CAT, enabled=True)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur, user_id=alice.id, actor_role="student")
        cur.execute(
            "UPDATE notification_preferences SET enabled = false WHERE id = %s", [bob_pref.pk]
        )
        assert cur.rowcount == 0  # filtered out by USING
        # Positive control: same session CAN update its own row.
        cur.execute(
            "UPDATE notification_preferences SET enabled = false WHERE id = %s", [alice_pref.pk]
        )
        assert cur.rowcount == 1

    with as_path_admin():
        bob_pref.refresh_from_db()
    assert bob_pref.enabled is True  # untouched


@pytest.mark.django_db(transaction=True)
def test_anonymous_session_sees_nothing(skip_if_sqlite):
    alice = _make_student("alice-notif@test.local")
    with as_path_admin():
        NotificationPreference.objects.create(user=alice, category=CAT, enabled=False)

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur)  # all empty — deny by default
        cur.execute("SELECT count(*) FROM notification_preferences")
        assert cur.fetchone()[0] == 0
        # Positive control in the same test: alice's GUCs DO reveal her row.
        _set_gucs(cur, user_id=alice.id, actor_role="student")
        cur.execute("SELECT count(*) FROM notification_preferences")
        assert cur.fetchone()[0] == 1


# ---------------------------------------------------------------------------
# Story 8.6 — `delta_recap_cursors` (same policy shape, migration 0006)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cross_user_delta_cursor_is_invisible_and_unwritable(skip_if_sqlite):
    from apps.notifications.models import DeltaRecapCursor

    alice = _make_student("alice-delta@test.local")
    bob = _make_student("bob-delta@test.local")
    with as_path_admin():
        DeltaRecapCursor.objects.create(user=alice, seen_at=timezone.now())
        bob_cursor = DeltaRecapCursor.objects.create(user=bob, seen_at=timezone.now())

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur, user_id=alice.id, actor_role="student")
        cur.execute("SELECT user_id FROM delta_recap_cursors")
        visible = {r[0] for r in cur.fetchall()}
        assert alice.id in visible  # positive control — the session is live
        assert bob.id not in visible, "RLS must hide other users' recap cursors."
        # Cross-user UPDATE matches nothing (USING filters it out).
        cur.execute("UPDATE delta_recap_cursors SET seen_at = now() WHERE id = %s", [bob_cursor.pk])
        assert cur.rowcount == 0
