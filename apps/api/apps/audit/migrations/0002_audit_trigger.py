"""Append-only trigger for `audit_logs` — PostgreSQL only.

Two `BEFORE` triggers refuse any UPDATE or DELETE with a P0001 RAISE EXCEPTION.
This is the DB-level immutability guarantee promised by NFR-S4. SQLite (test
fast path) is skipped — the manager-level checks in `apps/audit/models.py`
keep tests honest, and a dedicated `@pytest.mark.postgresql_only` test
validates the trigger end-to-end in the PG CI job.
"""

from django.db import migrations


CREATE_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION audit_logs_block_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs.%_blocked: rows are append-only', TG_OP
    USING ERRCODE = 'P0001';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;
CREATE TRIGGER audit_logs_no_update
  BEFORE UPDATE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit_logs_block_mutation();

DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs;
CREATE TRIGGER audit_logs_no_delete
  BEFORE DELETE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit_logs_block_mutation();
"""

DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;
DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs;
DROP FUNCTION IF EXISTS audit_logs_block_mutation();
"""


def apply_trigger(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(CREATE_TRIGGER_SQL)


def revert_trigger(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(DROP_TRIGGER_SQL)


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [migrations.RunPython(apply_trigger, revert_trigger)]
