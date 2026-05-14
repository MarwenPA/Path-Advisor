"""Idempotent extension provisioning.

`infra/postgres/init.sql` only runs on first boot of a fresh data volume.
Reusing an existing `postgres_data` volume across image upgrades would skip
those `CREATE EXTENSION` calls, leaving pgvector / pgcrypto absent. Running
the same statements as a Django migration guarantees they are applied no
matter how the DB was provisioned.

Skipped on SQLite (test settings) — `connection.vendor` guard.
"""

from django.db import migrations


def _create_extensions(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")


class Migration(migrations.Migration):
    initial = True
    dependencies = []  # type: ignore[var-annotated]
    operations = [migrations.RunPython(_create_extensions, reverse_code=migrations.RunPython.noop)]
