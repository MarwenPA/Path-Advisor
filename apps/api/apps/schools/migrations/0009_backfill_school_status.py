"""Story 9.2 — backfill editorial status from the legacy boolean (mirror of
professions 0007)."""

from __future__ import annotations

from django.db import migrations


def forwards(apps, schema_editor) -> None:
    School = apps.get_model("schools", "School")
    School.objects.filter(is_active=True).update(status="published")
    School.objects.filter(is_active=False).update(status="archived")


class Migration(migrations.Migration):
    dependencies = [("schools", "0008_school_status_schoolrevision")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
