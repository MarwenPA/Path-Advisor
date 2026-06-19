"""Bulletin upload + OCR job models — Story 2.3.

`Bulletin` — one uploaded file (PDF / JPEG / PNG / HEIC) per student trimestre.
`BulletinOCRJob` — async OCR job tied to a Bulletin, managed by Celery.

Tenant isolation follows Story 1.8 pattern (tenant_id denormalized).
RLS: students read/write only their own rows.

GDPR / HDS:
- `file_path` is an S3 key under `bulletins/{student_id}/` (SSE-S3 at rest).
- Bulletins never validated within 30 days are purged by `tasks_purge.py`.
- Raw OCR output + confidence stored separately from user corrections for
  audit longitudinal (Story 9.5).
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.db import models
from django.utils import timezone

from apps.core.ids import generate_id


def _default_bulletin_id() -> str:
    return generate_id("blt")


def _default_ocr_job_id() -> str:
    return generate_id("ocrj")


class UploadedStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    FAILED = "failed", "Upload failed"


class OCRJobStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    RUNNING = "running", "En cours"
    SUCCEEDED = "succeeded", "Succès"
    FAILED = "failed", "Échec"
    TIMEOUT = "timeout", "Timeout"


class OCRProvider(models.TextChoices):
    TESSERACT = "tesseract", "Tesseract"
    MINDEE = "mindee", "Mindee"
    TEXTRACT = "textract", "AWS Textract"


class Bulletin(models.Model):
    """One uploaded bulletin file per student.

    A student may upload up to 6 bulletins per onboarding session (3 trimestres
    × 2 years). Each file is stored on S3-compatible storage (MinIO local /
    S3 EU prod) with SSE-S3 encryption.

    `expires_at` is set to `uploaded_at + 30 days` at creation. A Celery beat
    task (`tasks_purge.py`) deletes bulletins where `expires_at < now() AND
    validated_at IS NULL` — GDPR storage-limitation principle.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_bulletin_id,
        editable=False,
    )
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="bulletins",
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    # S3 object key — never store the full URL (presigned URLs are ephemeral).
    file_path = models.CharField(max_length=512)
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.PositiveBigIntegerField()
    mime_type = models.CharField(max_length=100)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_status = models.CharField(
        max_length=10,
        choices=UploadedStatus.choices,
        default=UploadedStatus.UPLOADED,
    )

    # Snapshot of the student's level at upload time — needed for the subject
    # referential versioning (AC8 `subjects_ref_version`).
    level_at_upload = models.CharField(max_length=20, null=True, blank=True)
    subjects_ref_version = models.CharField(max_length=20, null=True, blank=True)

    validated_at = models.DateTimeField(null=True, blank=True)

    # GDPR: auto-purge after 30 days if never validated.
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bulletins"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["student", "uploaded_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"Bulletin({self.id}, student={self.student_id}, status={self.uploaded_status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.tenant_id is None and self.student_id:
            self.tenant_id = (
                type(self)
                .student.field.related_model.objects.filter(pk=self.student_id)
                .values_list("tenant_id", flat=True)
                .first()
            )
        if self.expires_at is None:
            from datetime import timedelta

            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def mark_validated(self) -> None:
        if self.validated_at is None:
            self.validated_at = timezone.now()
            self.expires_at = None  # No longer subject to purge


class BulletinOCRJob(models.Model):
    """Async OCR job for one Bulletin.

    Created by `POST /api/v1/students/me/bulletins/ocr/start`. The Celery
    worker updates `status`, `raw_extraction`, and `confidence_avg` once the
    job completes (or fails/times out).

    `raw_extraction` stores the full provider output as JSONB — never mutated
    after the job completes. Corrections applied by the student are stored
    separately in `BulletinCorrectedField` (or inline via PATCH /finalize).
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_ocr_job_id,
        editable=False,
    )
    bulletin = models.OneToOneField(
        Bulletin,
        on_delete=models.CASCADE,
        related_name="ocr_job",
    )

    status = models.CharField(
        max_length=10,
        choices=OCRJobStatus.choices,
        default=OCRJobStatus.PENDING,
        db_index=True,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Raw provider output — never mutated post-completion (audit longitudinal).
    raw_extraction = models.JSONField(null=True, blank=True)
    # Normalized extracted fields after fuzzy mapping.
    normalized_fields = models.JSONField(null=True, blank=True)
    # Average confidence across all extracted fields.
    confidence_avg = models.FloatField(null=True, blank=True)

    error_message = models.TextField(null=True, blank=True)
    provider = models.CharField(
        max_length=10,
        choices=OCRProvider.choices,
        default=OCRProvider.TESSERACT,
    )
    provider_version = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bulletin_ocr_jobs"

    def __str__(self) -> str:
        return f"BulletinOCRJob({self.id}, bulletin={self.bulletin_id}, status={self.status})"

    @property
    def is_low_quality(self) -> bool:
        """True if OCR output is too poor to present to the student.

        Triggers GracefulFallback on the front-end (AC7). Thresholds per spike doc:
        - confidence_avg < 0.3, OR
        - fewer than 3 subject fields extracted.
        """
        if self.status != OCRJobStatus.SUCCEEDED:
            return True
        if self.confidence_avg is not None and self.confidence_avg < 0.3:
            return True
        fields = self.normalized_fields or []
        subject_fields = [f for f in fields if f.get("key") == "matiere"]
        return len(subject_fields) < 3
