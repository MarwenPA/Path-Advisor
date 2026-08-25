"""Convert `level_compatibility` from postgres ArrayField to portable JSONField.

Root cause: `ArrayField` generates a `varchar(...)[]` column type that
SQLite's schema editor cannot create ("near '[]': syntax error"). Since
pytest-django builds the FULL test schema (all installed apps) for any
`@pytest.mark.django_db` test, this broke the SQLite fast lane
(`path_advisor.settings.test`) for every app in the repo, not just
`professions` — e.g. `apps/family` (Story 6.1), `apps/accounts`, etc.

Fix: swap to `models.JSONField` (already the pattern used everywhere else
on this model — `requirements_json`, `signals_json`, `sources_json`).
Values remain a plain Python list either way, so no callers change
(`apps.recommendations.services.recommendation_service`,
`ProfessionPublicSerializer` auto-mapping, `is_compatible_with_level`).

Migration strategy is deliberately portable (ORM copy via `RunPython`,
no raw `ALTER COLUMN ... TYPE ... USING`) so it applies identically on
SQLite and PostgreSQL:
  1. Add a new JSONField column.
  2. Copy every row's array value into it.
  3. Drop the old ArrayField column.
  4. Rename the new column to the original name.

The GIN index on `level_compatibility` was already removed in migration
0004; no index needs to be re-added here (see Story 3.2 dev notes — a
jsonb GIN index can be reintroduced as a Postgres-only follow-up if the
scoring engine's query patterns need it).
"""

from __future__ import annotations

from django.db import migrations, models


def _copy_array_to_json(apps, schema_editor):
    Profession = apps.get_model("professions", "Profession")
    for profession in Profession.objects.all().iterator():
        profession.level_compatibility_new = list(profession.level_compatibility or [])
        profession.save(update_fields=["level_compatibility_new"])


def _copy_json_to_array(apps, schema_editor):
    Profession = apps.get_model("professions", "Profession")
    for profession in Profession.objects.all().iterator():
        profession.level_compatibility = list(profession.level_compatibility_new or [])
        profession.save(update_fields=["level_compatibility"])


class Migration(migrations.Migration):
    dependencies = [
        ("professions", "0004_remove_profession_professions_signals_json_gin_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profession",
            name="level_compatibility_new",
            field=models.JSONField(default=list),
        ),
        migrations.RunPython(_copy_array_to_json, _copy_json_to_array),
        migrations.RemoveField(
            model_name="profession",
            name="level_compatibility",
        ),
        migrations.RenameField(
            model_name="profession",
            old_name="level_compatibility_new",
            new_name="level_compatibility",
        ),
        migrations.AlterField(
            model_name="profession",
            name="level_compatibility",
            field=models.JSONField(
                default=list,
                help_text=(
                    "Levels this profession is compatible with: college_3eme, lycee_2nde, "
                    "lycee_1ere_tle_general, lycee_1ere_tle_techno, lycee_1ere_tle_pro, postbac."
                ),
            ),
        ),
    ]
