"""Initial schema for `audit_logs` — append-only journal (Story 1.13).

The PostgreSQL trigger that enforces append-only at the DB level lives in
`0002_audit_trigger.py`. SQLite test runs only get the table and the manager-
level checks.
"""

from django.db import migrations, models

import apps.audit.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_init_extensions"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.audit.models._default_audit_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("actor_id", models.CharField(blank=True, db_index=True, max_length=32, null=True)),
                ("actor_role", models.CharField(db_index=True, default="", max_length=20)),
                ("tenant_id", models.UUIDField(blank=True, db_index=True, null=True)),
                (
                    "subject_id",
                    models.CharField(blank=True, db_index=True, max_length=32, null=True),
                ),
                ("action", models.CharField(db_index=True, max_length=100)),
                (
                    "result",
                    models.CharField(
                        choices=[
                            ("success", "Success"),
                            ("failure", "Failure"),
                            ("denied", "Denied"),
                        ],
                        db_index=True,
                        default="success",
                        max_length=20,
                    ),
                ),
                ("request_id", models.CharField(blank=True, max_length=32, null=True)),
                (
                    "ip_address_hash",
                    models.CharField(blank=True, max_length=64, null=True),
                ),
                ("user_agent", models.CharField(blank=True, max_length=255, null=True)),
                ("metadata", models.JSONField(default=dict)),
                ("prev_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("row_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(db_index=True)),
            ],
            options={
                "db_table": "audit_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["subject_id", "-created_at"], name="idx_audit_subject_created"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["actor_id", "-created_at"], name="idx_audit_actor_created"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["action", "-created_at"], name="idx_audit_action_created"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["tenant_id", "-created_at"], name="idx_audit_tenant_created"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["result", "-created_at"], name="idx_audit_result_created"
            ),
        ),
    ]
