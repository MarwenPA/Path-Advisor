"""Story 6.5 §AC6 — Row-Level Security on `establishments` + `cohorts` (PostgreSQL only).

Pattern copied from `apps.accounts.migrations.0007_enable_rls`:

- `path_admin` bypasses (back-office cross-tenant operations).
- `app.bypass_rls` bypasses (Celery jobs — `with_system_actor()`).
- `cohorts` ALSO grants same-tenant `counselor` READ-ONLY (story §AC6): a
  counselor sees the cohorts of their own establishment, but only
  `path_admin`/bypass can write (no same-tenant write policy — cohort
  modification stays path_admin-only for the MVP per story §6 Out of Scope).
- `establishments` has NO same-tenant policy at all — a counselor never
  reads the `Establishment` row directly (Epic 6.6+ will expose whatever
  establishment-level fields a cohort dashboard needs via a dedicated,
  narrower endpoint, not direct table access).

No `users` policy: Story 1.8's `users_isolation_select` already grants
same-tenant `SELECT` on `users`, and `Establishment.id` now populates
`tenant_id` there — no touch needed to that migration.
"""

from __future__ import annotations

from django.db import migrations

ENABLE_RLS_SQL = """
ALTER TABLE establishments ENABLE ROW LEVEL SECURITY;
ALTER TABLE establishments FORCE ROW LEVEL SECURITY;

ALTER TABLE cohorts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cohorts FORCE ROW LEVEL SECURITY;
"""

DISABLE_RLS_SQL = """
ALTER TABLE establishments NO FORCE ROW LEVEL SECURITY;
ALTER TABLE establishments DISABLE ROW LEVEL SECURITY;

ALTER TABLE cohorts NO FORCE ROW LEVEL SECURITY;
ALTER TABLE cohorts DISABLE ROW LEVEL SECURITY;
"""

CREATE_POLICIES_SQL = """
-- ESTABLISHMENTS --------------------------------------------------------
DROP POLICY IF EXISTS establishments_isolation_select ON establishments;
CREATE POLICY establishments_isolation_select ON establishments
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
    );

DROP POLICY IF EXISTS establishments_isolation_modify ON establishments;
CREATE POLICY establishments_isolation_modify ON establishments
    FOR ALL
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
    )
    WITH CHECK (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
    );

-- COHORTS -----------------------------------------------------------------
DROP POLICY IF EXISTS cohorts_isolation_select ON cohorts;
CREATE POLICY cohorts_isolation_select ON cohorts
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR (
            current_setting('app.actor_role', true) = 'counselor'
            AND tenant_id IS NOT NULL
            AND tenant_id::text = NULLIF(current_setting('app.current_tenant_id', true), '')
        )
    );

DROP POLICY IF EXISTS cohorts_isolation_modify ON cohorts;
CREATE POLICY cohorts_isolation_modify ON cohorts
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

DROP_POLICIES_SQL = """
DROP POLICY IF EXISTS establishments_isolation_select ON establishments;
DROP POLICY IF EXISTS establishments_isolation_modify ON establishments;
DROP POLICY IF EXISTS cohorts_isolation_select ON cohorts;
DROP POLICY IF EXISTS cohorts_isolation_modify ON cohorts;
"""


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
        ("establishments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_rls, revert_rls),
    ]
