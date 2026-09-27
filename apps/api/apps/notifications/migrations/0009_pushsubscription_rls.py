"""Story 10.2 — RLS on `push_subscriptions` (personal data: a minor's
device reachability). Policies mirror 0006/`delta_recap_cursors`
byte-for-byte in structure: owner via `app.current_user_id`, plus the
`path_admin` and `bypass_rls` branches.

Replayable: DROP POLICY IF EXISTS before every CREATE POLICY.
"""

from __future__ import annotations

from django.db import migrations

ENABLE_RLS_SQL = """
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions FORCE ROW LEVEL SECURITY;
"""

DISABLE_RLS_SQL = """
ALTER TABLE push_subscriptions NO FORCE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions DISABLE ROW LEVEL SECURITY;
"""

CREATE_POLICIES_SQL = """
-- SELECT --------------------------------------------------------------------
DROP POLICY IF EXISTS push_subscriptions_isolation_select ON push_subscriptions;
CREATE POLICY push_subscriptions_isolation_select ON push_subscriptions
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR user_id = current_setting('app.current_user_id', true)
    );

-- ALL (INSERT / UPDATE / DELETE) -------------------------------------------
DROP POLICY IF EXISTS push_subscriptions_isolation_modify ON push_subscriptions;
CREATE POLICY push_subscriptions_isolation_modify ON push_subscriptions
    FOR ALL
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR user_id = current_setting('app.current_user_id', true)
    )
    WITH CHECK (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR user_id = current_setting('app.current_user_id', true)
    );
"""

DROP_POLICIES_SQL = """
DROP POLICY IF EXISTS push_subscriptions_isolation_select ON push_subscriptions;
DROP POLICY IF EXISTS push_subscriptions_isolation_modify ON push_subscriptions;
"""


def apply_rls(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return  # SQLite fast lane has no RLS engine
    schema_editor.execute(ENABLE_RLS_SQL)
    schema_editor.execute(CREATE_POLICIES_SQL)


def revert_rls(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(DROP_POLICIES_SQL)
    schema_editor.execute(DISABLE_RLS_SQL)


class Migration(migrations.Migration):
    dependencies = [("notifications", "0008_pushsubscription")]
    operations = [migrations.RunPython(apply_rls, revert_rls)]
