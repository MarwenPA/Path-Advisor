"""Story 1.8 — Multi-tenant Row-Level Security (PostgreSQL only).

Three orthogonal changes ship together so a single `migrate` brings the DB to
a consistent RLS state:

1. **Schema (PG + SQLite):** add `tenant_id` to `parental_consents` and
   backfill it from `student.tenant_id`. The column itself is portable;
   the policies that key on it are PostgreSQL-only.

2. **RLS enable + FORCE (PG only):** `users` and `parental_consents` get
   `ROW LEVEL SECURITY` enabled. `FORCE` is critical — without it, the
   table owner (the Django app role) silently bypasses RLS and tests pass
   for the wrong reason.

3. **Named policies (PG only):** policies key on four session GUCs:

   - `app.current_user_id`, `app.current_tenant_id`, `app.actor_role`:
     populated by `TenantSessionMiddleware` (Story 1.8 T2) at request entry.
   - `app.bypass_rls`: opened by `apps.core.rls.bypass_rls()` /
     `with_system_actor()` (post-review D3/D4) for the narrow set of
     anonymous endpoints (signup signal, parental /decide/, status read)
     and system tasks (Celery beat) that legitimately need cross-row
     access without a `request.user`. Each entry is audited via the
     `rls.bypass_used` action.

4. **Anti-escalation trigger (PG only):** `users_block_privileged_field_update`
   BEFORE UPDATE on `users` raises if `role` or `tenant_id` change without
   `app.actor_role = 'path_admin'`. Belt-and-suspenders with the RLS modify
   policy — without it, the policy `id = current_user_id` would let a
   student promote themselves to `path_admin` and unlock the cross-tenant
   bypass (post-review D2).

`audit_logs` is intentionally NOT touched: cross-tenant by design (ADR-0009
§7, DPO oversight). `users` policies allow `path_admin` cross-tenant
visibility so the back-office (Story 1.13 + future 1.9/1.11/1.12) can
operate. `parental_consents` is stricter — even same-tenant counselors
must not read another student's parental consent.

Migration is replayable: every `CREATE POLICY` / `CREATE TRIGGER` is
preceded by `DROP IF EXISTS` so a partial apply + replay works.
"""

from __future__ import annotations

from django.db import migrations, models


# ---------------------------------------------------------------------------
# Step 2 — RLS enable + FORCE
# ---------------------------------------------------------------------------

ENABLE_RLS_SQL = """
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

ALTER TABLE parental_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE parental_consents FORCE ROW LEVEL SECURITY;
"""

DISABLE_RLS_SQL = """
ALTER TABLE users NO FORCE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

ALTER TABLE parental_consents NO FORCE ROW LEVEL SECURITY;
ALTER TABLE parental_consents DISABLE ROW LEVEL SECURITY;
"""

# ---------------------------------------------------------------------------
# Step 3 — Named policies
#
# `users` SELECT — laxe:
#   - path_admin role bypasses (back-office cross-tenant operations).
#   - whitelisted bypass via `app.bypass_rls` (anonymous flows, system tasks).
#   - any user can see their own row.
#   - same-tenant users see each other (counselor → cohort, Epic 6).
#
# `users` MODIFY — same shape; the trigger below enforces that role/tenant_id
#   changes need explicit `path_admin`.
#
# `parental_consents` — stricter:
#   - path_admin bypass.
#   - `app.bypass_rls` bypass.
#   - the owning student.
#
# `current_setting(name, true)` returns NULL when unset; combined with
# `current_setting(...) = 'literal'`, NULL ≠ literal so the row is denied.
# That's the "deny by default during migrations / anonymous" behaviour we want.
# ---------------------------------------------------------------------------

# `CREATE POLICY` does not natively support `IF NOT EXISTS` in PG ≤ 16, so we
# always `DROP IF EXISTS` first. Same pattern for the trigger function +
# trigger itself. Result: migration is fully replayable.
CREATE_POLICIES_SQL = """
-- USERS ---------------------------------------------------------------------
DROP POLICY IF EXISTS users_isolation_select ON users;
CREATE POLICY users_isolation_select ON users
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR id = current_setting('app.current_user_id', true)
        OR (
            tenant_id IS NOT NULL
            AND tenant_id::text = NULLIF(current_setting('app.current_tenant_id', true), '')
        )
    );

DROP POLICY IF EXISTS users_isolation_modify ON users;
CREATE POLICY users_isolation_modify ON users
    FOR ALL
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR id = current_setting('app.current_user_id', true)
    )
    WITH CHECK (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR id = current_setting('app.current_user_id', true)
    );

-- PARENTAL_CONSENTS ---------------------------------------------------------
DROP POLICY IF EXISTS parental_consents_isolation_select ON parental_consents;
CREATE POLICY parental_consents_isolation_select ON parental_consents
    FOR SELECT
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR student_id = current_setting('app.current_user_id', true)
    );

DROP POLICY IF EXISTS parental_consents_isolation_modify ON parental_consents;
CREATE POLICY parental_consents_isolation_modify ON parental_consents
    FOR ALL
    USING (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR student_id = current_setting('app.current_user_id', true)
    )
    WITH CHECK (
        current_setting('app.bypass_rls', true) = 'true'
        OR current_setting('app.actor_role', true) = 'path_admin'
        OR student_id = current_setting('app.current_user_id', true)
    );
"""

DROP_POLICIES_SQL = """
DROP POLICY IF EXISTS users_isolation_select ON users;
DROP POLICY IF EXISTS users_isolation_modify ON users;
DROP POLICY IF EXISTS parental_consents_isolation_select ON parental_consents;
DROP POLICY IF EXISTS parental_consents_isolation_modify ON parental_consents;
"""


# ---------------------------------------------------------------------------
# Step 4 — Anti-escalation trigger (post-review D2)
#
# RLS lets self-update via `id = current_user_id`. Without further guard, a
# student could `UPDATE users SET role = 'path_admin' WHERE id = self` and
# unlock the cross-tenant bypass. This trigger refuses any UPDATE that
# changes `role` OR `tenant_id` unless the caller asserts path_admin
# explicitly OR the audited bypass GUC is set (back-office migrations).
# ---------------------------------------------------------------------------

CREATE_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION users_block_privileged_field_update()
RETURNS trigger AS $$
BEGIN
    IF (NEW.role IS DISTINCT FROM OLD.role
        OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id)
       AND coalesce(current_setting('app.actor_role', true), '') != 'path_admin'
       AND coalesce(current_setting('app.bypass_rls', true), '') != 'true'
    THEN
        RAISE EXCEPTION
            'users.privileged_field_update_blocked: role / tenant_id '
            'changes require path_admin actor (got %)',
            coalesce(current_setting('app.actor_role', true), '')
            USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_block_privileged_field_update ON users;
CREATE TRIGGER users_block_privileged_field_update
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION users_block_privileged_field_update();
"""

DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS users_block_privileged_field_update ON users;
DROP FUNCTION IF EXISTS users_block_privileged_field_update();
"""


# ---------------------------------------------------------------------------
# Step 1 — Backfill data (portable: works on SQLite too)
# ---------------------------------------------------------------------------


def backfill_tenant_id(apps, schema_editor) -> None:
    """Copy each parental_consent's `tenant_id` from its student.

    Portable across SQLite + PostgreSQL: this is a plain ORM update, not raw
    SQL. Zero rows expected in non-dev environments at this point — Story 1.4
    just shipped — but the data step is mandatory for correctness on dev DBs.
    """
    ParentalConsent = apps.get_model("accounts", "ParentalConsent")
    rows = ParentalConsent.objects.filter(tenant_id__isnull=True).select_related("student")
    for row in rows:
        if row.student.tenant_id is not None:
            row.tenant_id = row.student.tenant_id
            row.save(update_fields=["tenant_id"])


def reverse_backfill_noop(apps, schema_editor) -> None:
    """Backfill is forward-only; reverse just nulls the column on rollback
    (handled by the AddField reversal). This RunPython reverse is a no-op."""


# ---------------------------------------------------------------------------
# Step 2+3+4 — PG-only RLS setup
# ---------------------------------------------------------------------------


def apply_rls(apps, schema_editor) -> None:
    """Enable RLS + create policies + install anti-escalation trigger."""
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(ENABLE_RLS_SQL)
        cursor.execute(CREATE_POLICIES_SQL)
        cursor.execute(CREATE_TRIGGER_SQL)


def revert_rls(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(DROP_TRIGGER_SQL)
        cursor.execute(DROP_POLICIES_SQL)
        cursor.execute(DISABLE_RLS_SQL)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_gdpr_export_unique_active"),
    ]

    operations = [
        # Step 1 — schema change is portable across both backends.
        migrations.AddField(
            model_name="parentalconsent",
            name="tenant_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(backfill_tenant_id, reverse_backfill_noop),
        # Steps 2 + 3 + 4 — PostgreSQL-only RLS setup.
        migrations.RunPython(apply_rls, revert_rls),
    ]
