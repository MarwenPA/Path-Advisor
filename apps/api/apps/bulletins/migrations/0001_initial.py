"""Initial migration for Bulletin + BulletinOCRJob models — Story 2.3."""

import apps.bulletins.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Bulletin",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.bulletins.models._default_bulletin_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("file_path", models.CharField(max_length=512)),
                ("original_filename", models.CharField(max_length=255)),
                ("file_size_bytes", models.PositiveBigIntegerField()),
                ("mime_type", models.CharField(max_length=100)),
                (
                    "uploaded_status",
                    models.CharField(
                        choices=[("uploaded", "Uploaded"), ("failed", "Upload failed")],
                        default="uploaded",
                        max_length=10,
                    ),
                ),
                ("level_at_upload", models.CharField(blank=True, max_length=20, null=True)),
                ("subjects_ref_version", models.CharField(blank=True, max_length=20, null=True)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bulletins",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "bulletins"},
        ),
        migrations.CreateModel(
            name="BulletinOCRJob",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.bulletins.models._default_ocr_job_id,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("running", "En cours"),
                            ("succeeded", "Succès"),
                            ("failed", "Échec"),
                            ("timeout", "Timeout"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("raw_extraction", models.JSONField(blank=True, null=True)),
                ("normalized_fields", models.JSONField(blank=True, null=True)),
                ("confidence_avg", models.FloatField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("tesseract", "Tesseract"),
                            ("mindee", "Mindee"),
                            ("textract", "AWS Textract"),
                        ],
                        default="tesseract",
                        max_length=10,
                    ),
                ),
                ("provider_version", models.CharField(blank=True, max_length=20, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "bulletin",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ocr_job",
                        to="bulletins.bulletin",
                    ),
                ),
            ],
            options={"db_table": "bulletin_ocr_jobs"},
        ),
        migrations.AddIndex(
            model_name="bulletin",
            index=models.Index(
                fields=["student", "uploaded_at"], name="bulletins_student_uploaded_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="bulletin",
            index=models.Index(fields=["expires_at"], name="bulletins_expires_at_idx"),
        ),
    ]
