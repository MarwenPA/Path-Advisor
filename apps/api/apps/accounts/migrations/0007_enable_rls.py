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

3. **Named policies (PG only):** policies key on three session GUCs that
   `TenantSessionMiddleware` (Story 1.8 T2) populates at request entry:
   `app.current_user_id`, `app.current_tenant_id`, `app.actor_role`.
   `current_setting(name, true)` returns NULL when unset, which the
   policies treat as a deny — important during migrations themselves
   (no request, no GUCs).

`audit_logs` is intentionally NOT touched: cross-tenant by design (ADR-0009
§7, DPO oversight). `users` policies allow `path_admin` cross-tenant
visibility so the back-office (Story 1.13 + future 1.9/1.11/1.12) can
operate. `parental_consents` is stricter — even same-tenant counselors
must not read another student's parental consent.
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
# `users`:
#   - path_admin role bypasses (back-office cross-tenant operations).
#   - any user can see their own row.
#   - same-tenant users see each other (counselor → cohort, Epic 6).
#
# `parental_consents`:
#   - path_admin role bypasses.
#   - the owning student sees their own consent rows.
#   - parents authenticated via the URL-safe token DON'T pass through this
#     middleware — the parental_consent views run as anonymous and rely on
#     the explicit token lookup. RLS in their case sees actor_role='' and
#     denies — that's why the parental-consent endpoints are decorated
#     `@permission_classes([AllowAny])` and the views set the GUC themselves
#     (out-of-band for the specific token row only; this is the documented
#     bypass in §4.7 / Story 1.4).
#
# Note: `current_setting(name, true)` returns NULL when unset; combined with
# `current_setting(...) = 'literal'`, NULL ≠ literal so the row is denied.
# That's exactly the "deny by default during migrations" behaviour we want.
# ---------------------------------------------------------------------------

CREATE_POLICIES_SQL = """
-- USERS ---------------------------------------------------------------------
CREATE POLICY users_isolation_select ON users
    FOR SELECT
    USING (
        current_setting('app.actor_role', true) = 'path_admin'
        OR id = current_setting('app.current_user_id', true)
        OR (
            tenant_id IS NOT NULL
            AND tenant_id::text = NULLIF(current_setting('app.current_tenant_id', true), '')
        )
    );

CREATE POLICY users_isolation_modify ON users
    FOR ALL
    USING (
        current_setting('app.actor_role', true) = 'path_admin'
        OR id = current_setting('app.current_user_id', true)
    )
    WITH CHECK (
        current_setting('app.actor_role', true) = 'path_admin'
        OR id = current_setting('app.current_user_id', true)
    );

-- PARENTAL_CONSENTS ---------------------------------------------------------
-- Stricter: same-tenant alone is NOT enough — must be the owning student.
-- Parents authenticated by token aren't in `request.user`; their views
-- already bypass at the application layer via token lookup.
CREATE POLICY parental_consents_isolation_select ON parental_consents
    FOR SELECT
    USING (
        current_setting('app.actor_role', true) = 'path_admin'
        OR student_id = current_setting('app.current_user_id', true)
    );

CREATE POLICY parental_consents_isolation_modify ON parental_consents
    FOR ALL
    USING (
        current_setting('app.actor_role', true) = 'path_admin'
        OR student_id = current_setting('app.current_user_id', true)
    )
    WITH CHECK (
        current_setting('app.actor_role', true) = 'path_admin'
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
# Step 2+3 — PG-only RLS setup
# ---------------------------------------------------------------------------


def apply_rls(apps, schema_editor) -> None:
    """Enable RLS + create policies. Mirrors the audit-trigger guard pattern."""
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
        # Steps 2 + 3 — PostgreSQL-only RLS setup.
        migrations.RunPython(apply_rls, revert_rls),
    ]
