"""Story 9.5 — RLS on `scoring_decisions` (a minor's vocational inputs are
personal data; policies mirror notifications/0002) + seed the historical
model version.

The seed's `dataset_hash` is the honest marker "unversioned-legacy": nobody
hashed the calibration dataset when 0.3.0 shipped — later versions compute
a real SHA256 at registration.
"""

from __future__ import annotations

from django.db import migrations

ENABLE_RLS_SQL = """
ALTER TABLE scoring_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE scoring_decisions FORCE ROW LEVEL SECURITY;
"""

DISABLE_RLS_SQL = """
ALTER TABLE scoring_decisions NO FORCE ROW LEVEL SECURITY;
ALTER TABLE scoring_decisions DISABLE ROW LEVEL SECURITY;
"""

CREATE_POLICIES_SQL = """
DROP POLICY IF EXISTS scoring_decisions_isolation_select ON scoring_decisions;
CREATE POLICY scoring_decisions_isolation_select ON scoring_decisions
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR user_id = current_setting('app.current_user_id', true)
    );

DROP POLICY IF EXISTS scoring_decisions_isolation_modify ON scoring_decisions;
CREATE POLICY scoring_decisions_isolation_modify ON scoring_decisions
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
DROP POLICY IF EXISTS scoring_decisions_isolation_select ON scoring_decisions;
DROP POLICY IF EXISTS scoring_decisions_isolation_modify ON scoring_decisions;
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


def seed_legacy_version(apps, schema_editor) -> None:
    ModelVersion = apps.get_model("recommendations", "ModelVersion")
    ModelVersion.objects.get_or_create(
        version="0.3.0-statistical",
        defaults={
            "name": "Scorer statistique 3.3",
            "dataset_hash": "unversioned-legacy",
            "hyperparameters_json": {
                "passions": 0.30,
                "valeurs": 0.20,
                "niveau_compatibility": 0.15,
                "specialites": 0.15,
                "bulletin_quality": 0.20,
            },
            "evaluation_metrics_json": {},
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("recommendations", "0002_modelversion_scoringdecision")]
    operations = [
        migrations.RunPython(apply_rls, revert_rls),
        migrations.RunPython(seed_legacy_version, migrations.RunPython.noop),
    ]
