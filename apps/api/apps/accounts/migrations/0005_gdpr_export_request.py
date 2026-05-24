# Generated for Story 1.11 — GDPR Article 20 portability.

import apps.accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_parental_consent_review_columns"),
    ]

    operations = [
        migrations.CreateModel(
            name="GdprExportRequest",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.accounts.models._default_gdpr_export_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("user_id", models.CharField(db_index=True, max_length=32)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("in_progress", "En cours"),
                            ("ready", "Prêt"),
                            ("expired", "Expiré"),
                            ("failed", "Échec"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("requested_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ready_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("archive_s3_key", models.CharField(blank=True, max_length=512, null=True)),
                ("manifest_s3_key", models.CharField(blank=True, max_length=512, null=True)),
                ("archive_sha256", models.CharField(blank=True, max_length=64, null=True)),
                ("archive_size_bytes", models.BigIntegerField(blank=True, null=True)),
                ("password_hash", models.CharField(blank=True, max_length=128, null=True)),
                ("error_code", models.CharField(blank=True, max_length=50, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("download_count", models.PositiveIntegerField(default=0)),
                ("last_downloaded_at", models.DateTimeField(blank=True, null=True)),
                ("emails_sent_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "gdpr_export_requests",
                "ordering": ["-requested_at"],
                "indexes": [
                    models.Index(
                        fields=["user_id", "-requested_at"],
                        name="idx_gdpr_exports_user_req",
                    ),
                    models.Index(
                        fields=["status", "expires_at"],
                        name="idx_gdpr_exports_status_exp",
                    ),
                ],
            },
        ),
    ]
