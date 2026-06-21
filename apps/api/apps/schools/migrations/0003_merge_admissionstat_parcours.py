"""Merge migration — unify Story 4.2 (AdmissionStat) and Story 4.3 (Parcours) leaf migrations."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0002_admissionstat"),
        ("schools", "0002_parcours"),
    ]

    operations = []
