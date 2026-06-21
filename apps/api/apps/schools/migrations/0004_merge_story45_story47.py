"""Merge migration — unify Story 4.5 merge (admissionstat+parcours) and Story 4.7 parcours changes."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0003_merge_admissionstat_parcours"),
        ("schools", "0003_parcours_story47"),
    ]

    operations = []
