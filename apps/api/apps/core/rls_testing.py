"""Test-only RLS helpers — **MUST NOT be imported by production code**.

Story 1.16. The `rls` / `postgresql_only` lane runs as a
`NOSUPERUSER NOBYPASSRLS` role against tables carrying
`FORCE ROW LEVEL SECURITY`, so *even the table owner* is subject to the
policies. That is the entire point of the lane — see the
`_assert_non_superuser_in_postgres_lane` guard in the root `conftest.py`,
which hard-fails the suite if the role could bypass RLS.

The consequence went unnoticed for as long as the lane never ran (it had
never once been green in CI): a test's **arrange** phase cannot `INSERT`
into a protected table unless it first identifies itself to the policies.
`User.objects.create(...)` in test setup fails with
`new row violates row-level security policy for table "users"`.

`as_path_admin()` opens `app.actor_role = 'path_admin'` for the duration of
the block. Every RLS policy in this codebase carries a `path_admin` branch
(verified across `accounts/0007_enable_rls`, `students/0001_initial`,
`establishments/0002_enable_rls` and `0003_enable_rls_invitations_and_jobs`),
so this suffices for setup.

**Why `path_admin` and not `bypass_rls()`**: `apps.core.rls.bypass_rls()`
documents an explicit anti-pattern — *"DO NOT call bypass_rls() from a
generic helper. The set of call sites MUST stay countable on one hand."*
Using it from test fixtures would blow up exactly the grep surface a
reviewer relies on, and emit an audit row per test. Reusing an existing
legitimate policy branch adds no new bypass surface at all.

**Why SESSION scope, not transaction-local**: these tests use
`@pytest.mark.django_db(transaction=True)`, i.e. autocommit, so each ORM
call is its own transaction. A `set_config(..., is_local => true)` would
expire before the next statement. The autouse `RESET ALL` in `conftest.py`
clears the session between tests.

**Safety property** (the reason this is acceptable at all): every act
phase re-sets ALL of the GUCs transaction-locally inside
`transaction.atomic()`, and a transaction-local `set_config` overrides the
session value for the assertion window — verified empirically (Story 1.16):
deleting this helper's `finally` reset changed nothing, because the acts
pin their own session identity; whereas letting the privilege into an act
(`actor_role='path_admin'` in an act's `_set_gucs`) turns the suite RED
(`assert other_user.id not in visible_ids` breaks — path_admin sees every
row). A leak can therefore be neutralized or loud; it cannot make this
suite falsely green — provided act phases keep setting all three GUCs
explicitly, never relying on session state.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection


def _set_session_actor_role(value: str) -> None:
    """`set_config` at session scope (`is_local => false`). No-op off Postgres."""
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.actor_role', %s, false)", [value])


@contextmanager
def as_path_admin() -> Iterator[None]:
    """Run an arrange-phase block under `app.actor_role = 'path_admin'`.

    Wrap **only** test setup. Never wrap the behaviour under assertion —
    see this module's docstring for why a leak is loud rather than silent,
    and why that is what makes this helper safe.
    """
    _set_session_actor_role("path_admin")
    try:
        yield
    finally:
        _set_session_actor_role("")
