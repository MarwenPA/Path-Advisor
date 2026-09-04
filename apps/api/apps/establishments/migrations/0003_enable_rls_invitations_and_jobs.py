"""Code-review fix (2026-09) — RLS on `counselor_invitations`,
`student_import_invitations`, `cohort_import_jobs` (PostgreSQL only).

Migration 0002 enabled RLS on `establishments` + `cohorts` but left these
three tables — added in the same Story 6.5 — completely unprotected. All
three carry data rattached to a tenant (an invitation token in the clear,
a CSV import's per-row error report) with no defense-in-depth if a future
story (6.6+) exposes a counselor-facing view that forgets an explicit
`cohort__tenant_id` / `establishment_id` filter: a counselor of tenant B
would be able to read tenant A's invitation tokens directly from the DB
and take over a counselor/student account.

None of these three tables has its own `tenant_id` column (they only FK to
`cohort`/`establishment`), and there is no current product requirement for
same-tenant counselor read access to them (invitations are only ever
touched via the anonymous, `bypass_rls`-wrapped accept endpoints, or by
`path_admin` for creation/polling — already gated by `IsPathAdmin` at the
view layer). So the policy shape mirrors `establishments` itself
(migration 0002): `path_admin` / `app.bypass_rls` only, no same-tenant
branch. Revisit if/when a counselor-facing feature needs direct read
access to one of these tables — do not just relax this defensively; add a
real subquery-based same-tenant policy at that point.
"""

from __future__ import annotations

from django.db import migrations

_TABLES = ["counselor_invitations", "student_import_invitations", "cohort_import_jobs"]

ENABLE_RLS_SQL = "\n".join(
    f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;\nALTER TABLE {table} FORCE ROW LEVEL SECURITY;"
    for table in _TABLES
)

DISABLE_RLS_SQL = "\n".join(
    f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;\nALTER TABLE {table} DISABLE ROW LEVEL SECURITY;"
    for table in _TABLES
)


def _policy_sql(table: str) -> str:
    return f"""
DROP POLICY IF EXISTS {table}_isolation_select ON {table};
CREATE POLICY {table}_isolation_select ON {table}
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
    );

DROP POLICY IF EXISTS {table}_isolation_modify ON {table};
CREATE POLICY {table}_isolation_modify ON {table}
    FOR ALL
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
    )
    WITH CHECK (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
    );
"""


CREATE_POLICIES_SQL = "\n".join(_policy_sql(table) for table in _TABLES)

DROP_POLICIES_SQL = "\n".join(
    f"DROP POLICY IF EXISTS {table}_isolation_select ON {table};\n"
    f"DROP POLICY IF EXISTS {table}_isolation_modify ON {table};"
    for table in _TABLES
)


def apply_rls(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(ENABLE_RLS_SQL)
        cursor.execute(CREATE_POLICIES_SQL)


def revert_rls(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(DROP_POLICIES_SQL)
        cursor.execute(DISABLE_RLS_SQL)


class Migration(migrations.Migration):
    dependencies = [
        ("establishments", "0002_enable_rls"),
    ]

    operations = [
        migrations.RunPython(apply_rls, revert_rls),
    ]
