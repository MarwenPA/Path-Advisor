"""Story 1.10 review P1 — widen ``AuditLog.subject_id`` to 96 chars.

Composite ids `<source_name>:<source_pk>` (e.g.,
``parental_consent:<26-char-ULID>`` = 47 chars) overflow the old 32-char
limit ; PostgreSQL raises ``DataError`` on INSERT and ``record_audit``
swallows it, silently losing the audit row.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_audit_trigger"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="subject_id",
            field=models.CharField(blank=True, db_index=True, max_length=96, null=True),
        ),
    ]
