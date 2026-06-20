"""Add GIN indexes on signals_json and level_compatibility — Story 3.2 AC1."""

from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("professions", "0001_profession_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="profession",
            index=GinIndex(
                fields=["signals_json"],
                name="professions_signals_json_gin",
            ),
        ),
        migrations.AddIndex(
            model_name="profession",
            index=GinIndex(
                fields=["level_compatibility"],
                name="professions_level_compat_gin",
            ),
        ),
    ]
