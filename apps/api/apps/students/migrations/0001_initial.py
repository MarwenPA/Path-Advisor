"""Story 2.1 — initial `student_profiles` table + RLS policies.

Follows the Story 1.8 pattern (`accounts.0007_enable_rls`):
- Schema is portable across SQLite and PostgreSQL.
- RLS enable + FORCE + named policies are PostgreSQL-only and idempotent
  (`DROP POLICY IF EXISTS` before every `CREATE POLICY`).
- Migration is replayable: a partial apply followed by `migrate` should
  reach the same final state without manual intervention.

Policies — the student profile carries strictly personal declarative data
(passions, valeurs, intérêts). Read/write must be limited to:
- the owning student themselves (`user_id = current_setting('app.current_user_id')`),
- `path_admin` cross-tenant for the back-office (Story 1.13 audit views,
  future Story 1.9 access-list, future 1.10 revocation),
- the `app.bypass_rls` GUC opened by `apps.core.rls.bypass_rls()` /
  `with_system_actor()` for the narrow set of audited bypass cases
  (currently none for this table — the policy ships future-proof).

Counselors (Epic 6) are explicitly NOT given same-tenant access — a
student's declarative profile is stricter than their User row. Granting
counselor access will require an explicit policy revision plus an ADR.
"""

from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models

import apps.students.models


ENABLE_RLS_SQL = """
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles FORCE ROW LEVEL SECURITY;
"""

DISABLE_RLS_SQL = """
ALTER TABLE student_profiles NO FORCE ROW LEVEL SECURITY;
ALTER TABLE student_profiles DISABLE ROW LEVEL SECURITY;
"""

CREATE_POLICIES_SQL = """
-- SELECT --------------------------------------------------------------------
DROP POLICY IF EXISTS student_profiles_isolation_select ON student_profiles;
CREATE POLICY student_profiles_isolation_select ON student_profiles
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR user_id = current_setting('app.current_user_id', true)
    );

-- ALL (INSERT / UPDATE / DELETE) -------------------------------------------
DROP POLICY IF EXISTS student_profiles_isolation_modify ON student_profiles;
CREATE POLICY student_profiles_isolation_modify ON student_profiles
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
DROP POLICY IF EXISTS student_profiles_isolation_select ON student_profiles;
DROP POLICY IF EXISTS student_profiles_isolation_modify ON student_profiles;
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
        ("accounts", "0007_enable_rls"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentProfile",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.students.models._default_profile_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("passions", models.JSONField(blank=True, default=list)),
                ("valeurs", models.JSONField(blank=True, default=list)),
                (
                    "interets",
                    models.JSONField(blank=True, default=apps.students.models._default_interets),
                ),
                (
                    "onboarding_step1_status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("in_progress", "En cours"),
                            ("completed", "Terminé"),
                            ("skipped", "Reporté"),
                            ("partial_skipped", "Partiellement reporté"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("onboarding_step1_completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_profile",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "db_table": "student_profiles",
                "indexes": [
                    models.Index(fields=["onboarding_step1_status"], name="student_pro_onboard_e57bf3_idx"),
                ],
            },
        ),
        migrations.RunPython(apply_rls, revert_rls),
    ]
