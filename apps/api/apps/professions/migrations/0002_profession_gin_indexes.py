"""Add GIN indexes on signals_json and level_compatibility — Story 3.2 AC1.

Neutralized post-hoc (2026-08): `GinIndex` emits PostgreSQL-only
`CREATE INDEX ... USING gin (...)` SQL with no SQLite fallback, which broke
the SQLite fast test lane for the whole repo when replaying migration
history from scratch. Migration 0004 already removes both these indexes
two migrations later, so the net effect on any already-migrated environment
is unchanged — this file is kept (not deleted) only to preserve the
migration dependency chain / numbering for environments that already
recorded it as applied. See migration 0005 for the related
`level_compatibility` field-type fix.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("professions", "0001_profession_initial"),
    ]

    operations: list = []
