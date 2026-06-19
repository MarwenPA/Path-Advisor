"""Celery tasks for OCR processing — Story 2.3 T3.

`ocr_extract(bulletin_id)`:
  - Fetches file from S3
  - Converts HEIC → JPEG if needed
  - Runs Tesseract (PoC) or Mindee/Textract (prod)
  - Applies fuzzy subject mapping
  - Updates BulletinOCRJob with results
  - Emits audit events (Story 1.13)

The task is idempotent: re-running it on an already-completed job is a no-op.

Timeout: 60 s hard limit enforced via Celery `time_limit`.
"""

from __future__ import annotations

import io
import logging
import time

import boto3
from botocore.config import Config
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.bulletins.fuzzy_subject_mapper import map_subject
from apps.bulletins.models import BulletinOCRJob, OCRJobStatus
from apps.bulletins.providers.tesseract import TesseractProvider

log = logging.getLogger(__name__)

_provider = TesseractProvider()


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


def _convert_heic_if_needed(file_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Convert HEIC to JPEG using pillow-heif. No-op for other formats."""
    if mime_type not in ("image/heic", "image/heif"):
        return file_bytes, mime_type
    try:
        from PIL import Image
        from pillow_heif import register_heif_opener

        register_heif_opener()
        img = Image.open(io.BytesIO(file_bytes))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=92)
        return buf.getvalue(), "image/jpeg"
    except Exception as exc:
        log.warning("HEIC conversion failed: %s — proceeding with original bytes", exc)
        return file_bytes, mime_type


@shared_task(
    bind=True,
    max_retries=0,  # We handle retry logic at the endpoint level, not task level
    time_limit=60,
    soft_time_limit=55,
    name="bulletins.ocr_extract",
)
def ocr_extract(self, bulletin_id: str) -> dict:  # noqa: ARG001
    """Run OCR on a single bulletin file and persist the result.

    Returns a summary dict for logging/monitoring.
    """
    from apps.bulletins.models import Bulletin

    try:
        job = BulletinOCRJob.objects.select_related("bulletin").get(
            bulletin_id=bulletin_id
        )
    except BulletinOCRJob.DoesNotExist:
        log.error("OCR job not found for bulletin_id=%s", bulletin_id)
        return {"status": "missing_job", "bulletin_id": bulletin_id}

    # Idempotency guard
    if job.status in (OCRJobStatus.SUCCEEDED, OCRJobStatus.FAILED, OCRJobStatus.TIMEOUT):
        return {"status": "already_done", "job_id": job.id, "job_status": job.status}

    try:
        bulletin = job.bulletin
    except Exception:
        log.error("OCR job %s has no associated bulletin — aborting", job.id)
        return {"status": "missing_bulletin", "job_id": job.id}

    job.status = OCRJobStatus.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    start = time.monotonic()

    try:
        # Fetch file from S3
        s3 = _get_s3_client()
        bucket = settings.BULLETINS_BUCKET
        response = s3.get_object(Bucket=bucket, Key=bulletin.file_path)
        file_bytes = response["Body"].read()

        # HEIC conversion
        file_bytes, mime_type = _convert_heic_if_needed(file_bytes, bulletin.mime_type)

        # OCR extraction
        result = _provider.extract(file_bytes, mime_type)

        # Apply fuzzy subject mapping to matière fields
        normalized_fields = []
        for f in result.fields:
            field_dict = {"key": f.key, "value": f.value, "confidence": f.confidence}
            if f.key == "matiere":
                mapping = map_subject(f.value)
                field_dict.update(mapping)
            normalized_fields.append(field_dict)

        job.status = OCRJobStatus.SUCCEEDED
        job.completed_at = timezone.now()
        job.raw_extraction = result.to_dict()
        job.normalized_fields = normalized_fields
        job.confidence_avg = result.confidence_avg
        job.provider = result.provider
        job.provider_version = result.provider_version
        job.save()

        # Audit log
        record_audit(
            action="ocr_succeeded",
            result=AuditResult.SUCCESS,
            subject_id=str(bulletin.student_id),
            metadata={
                "bulletin_id": bulletin_id,
                "job_id": job.id,
                "provider": result.provider,
                "processing_ms": result.processing_ms,
                "confidence_avg": result.confidence_avg,
                "field_count": len(normalized_fields),
                "is_low_quality": job.is_low_quality,
            },
        )

        if job.is_low_quality:
            record_audit(
                action="ocr_failed_low_confidence",
                result=AuditResult.FAILURE,
                subject_id=str(bulletin.student_id),
                metadata={
                    "bulletin_id": bulletin_id,
                    "confidence_avg": result.confidence_avg,
                    "field_count": len(normalized_fields),
                },
            )

        return {
            "status": "succeeded",
            "job_id": job.id,
            "confidence_avg": result.confidence_avg,
            "field_count": len(normalized_fields),
            "is_low_quality": job.is_low_quality,
        }

    except Exception as exc:
        elapsed = time.monotonic() - start
        is_timeout = elapsed >= 55

        job.status = OCRJobStatus.TIMEOUT if is_timeout else OCRJobStatus.FAILED
        job.completed_at = timezone.now()
        job.error_message = str(exc)[:500]
        job.save(update_fields=["status", "completed_at", "error_message"])

        record_audit(
            action="ocr_failed_low_confidence",
            result=AuditResult.FAILURE,
            subject_id=str(bulletin.student_id),
            metadata={
                "bulletin_id": bulletin_id,
                "error": str(exc)[:200],
                "is_timeout": is_timeout,
            },
        )

        log.exception("OCR failed for bulletin_id=%s", bulletin_id)
        return {"status": "failed", "job_id": job.id, "error": str(exc)[:200]}
