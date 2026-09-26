"""Story 9.1 — backfill the editorial status from the legacy boolean.

`is_active=True → published`, `False → archived` (nothing in the existing
referential is a draft: everything was either live or soft-hidden).
"""

from __future__ import annotations

from django.db import migrations


def forwards(apps, schema_editor) -> None:
    Profession = apps.get_model("professions", "Profession")
    Profession.objects.filter(is_active=True).update(status="published")
    Profession.objects.filter(is_active=False).update(status="archived")


def backwards(apps, schema_editor) -> None:
    # `is_active` was never dropped — nothing to restore.
    pass


class Migration(migrations.Migration):
    dependencies = [("professions", "0006_profession_status_professionrevision")]
    operations = [migrations.RunPython(forwards, backwards)]
