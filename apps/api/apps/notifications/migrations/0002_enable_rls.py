"""Story 8.2 — RLS on `notification_preferences` (personal data: who wants
what emails is a preference profile). Policies mirror
`students/0001_initial` byte-for-byte in structure: owner via
`app.current_user_id`, plus the `path_admin` and `bypass_rls` branches the
whole codebase relies on (the unsubscribe endpoint uses the latter through
its nominal `bypass_rls(reason=...)` call site).

Replayable: DROP POLICY IF EXISTS before every CREATE POLICY.
"""

from __future__ import annotations

from django.db import migrations

ENABLE_RLS_SQL = """
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences FORCE ROW LEVEL SECURITY;
"""

DISABLE_RLS_SQL = """
ALTER TABLE notification_preferences NO FORCE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences DISABLE ROW LEVEL SECURITY;
"""

CREATE_POLICIES_SQL = """
-- SELECT --------------------------------------------------------------------
DROP POLICY IF EXISTS notification_preferences_isolation_select ON notification_preferences;
CREATE POLICY notification_preferences_isolation_select ON notification_preferences
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR user_id = current_setting('app.current_user_id', true)
    );

-- ALL (INSERT / UPDATE / DELETE) -------------------------------------------
DROP POLICY IF EXISTS notification_preferences_isolation_modify ON notification_preferences;
CREATE POLICY notification_preferences_isolation_modify ON notification_preferences
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
DROP POLICY IF EXISTS notification_preferences_isolation_select ON notification_preferences;
DROP POLICY IF EXISTS notification_preferences_isolation_modify ON notification_preferences;
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
    dependencies = [("notifications", "0001_initial")]
    operations = [migrations.RunPython(apply_rls, revert_rls)]
