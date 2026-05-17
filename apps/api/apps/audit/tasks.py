"""Celery tasks for periodic audit maintenance.

Scheduling is configured in `path_advisor/celery.py` so the schedule lives next
to the broker bootstrap; the tasks themselves stay close to their domain.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import timedelta
from typing import Any

import boto3
import structlog
from botocore.config import Config as BotoConfig
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.audit.decorators import record_audit
from apps.audit.models import AuditLog, AuditResult
from apps.audit.services.archive_service import archive_logs_older_than
from apps.audit.services.hash_chain import verify_chain

log = structlog.get_logger(__name__)


@shared_task(name="audit.archive_old_logs")
def archive_old_logs() -> dict[str, Any]:
    """Push entries older than `AUDIT_ARCHIVE_AFTER_DAYS` to S3 — does not delete from DB."""
    days = getattr(settings, "AUDIT_ARCHIVE_AFTER_DAYS", 3 * 365)
    manifest = archive_logs_older_than(days=days)
    if manifest is None:
        log.info("audit.archive_skipped", reason="no_rows")
        return {"archived": 0}
    log.info(
        "audit.archive_completed",
        row_count=manifest.row_count,
        archive_key=manifest.archive_key,
    )
    return {
        "archived": manifest.row_count,
        "archive_key": manifest.archive_key,
        "manifest_key": manifest.manifest_key,
    }


@shared_task(name="audit.verify_chain_integrity")
def verify_chain_integrity(window_days: int = 365) -> dict[str, Any]:
    """Recompute the SHA-256 chain over recent rows; alert on any break."""
    cutoff = timezone.now() - timedelta(days=window_days)
    rows = list(AuditLog.objects.filter(created_at__gte=cutoff).order_by("created_at"))
    broken = verify_chain(rows)
    if broken:
        log.error("audit.chain_break_detected", broken_ids=broken, verified_count=len(rows))
        try:
            import sentry_sdk

            sentry_sdk.capture_message(
                f"audit.chain_break_detected: {len(broken)} broken row(s)",
                level="error",
            )
        except Exception:
            pass
    else:
        log.info("audit.chain_verified", verified_count=len(rows))

    record_audit(
        action="audit.integrity_check_completed",
        result=AuditResult.SUCCESS if not broken else AuditResult.FAILURE,
        metadata={"verified_rows": len(rows), "broken_rows": broken},
    )
    return {"verified_rows": len(rows), "broken_rows": broken}


@shared_task(name="audit.export_csv_to_s3")
def export_csv_to_s3(filters: dict, requested_by: str) -> dict[str, Any]:
    """Build a CSV export, push it to the GDPR-exports S3 bucket, and return
    a presigned URL valid for `AUDIT_EXPORT_PRESIGNED_TTL_SECONDS` (Story 1.13 §AC5).

    Filter parsing mirrors the view to avoid a circular import; `from`/`to`
    must be parsed here too (the view-side `parse_datetime` does not carry
    over into the Celery serialisation boundary).
    """
    from django.utils.dateparse import (
        parse_datetime,  # local import — avoids settings dep at module load
    )

    qs = AuditLog.objects.all().order_by("created_at")
    for key in ("subject_id", "actor_id", "result"):
        if value := filters.get(key):
            qs = qs.filter(**{key: value})
    if value := filters.get("tenant_id"):
        # `tenant_id` is a UUIDField — let DB raise rather than 500 the worker.
        qs = qs.filter(tenant_id=value)
    if value := filters.get("action"):
        if isinstance(value, str) and value.endswith("."):
            qs = qs.filter(action__startswith=value)
        else:
            qs = qs.filter(action=value)
    if value := filters.get("from"):
        dt = parse_datetime(value) if isinstance(value, str) else value
        if dt:
            qs = qs.filter(created_at__gte=dt)
    if value := filters.get("to"):
        dt = parse_datetime(value) if isinstance(value, str) else value
        if dt:
            qs = qs.filter(created_at__lte=dt)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        (
            "id",
            "created_at",
            "actor_id",
            "actor_role",
            "subject_id",
            "action",
            "result",
            "tenant_id",
            "metadata_json",
        )
    )
    row_count = 0
    for row in qs.iterator(chunk_size=500):
        writer.writerow(
            (
                row.id,
                row.created_at.isoformat(),
                row.actor_id or "",
                row.actor_role,
                row.subject_id or "",
                row.action,
                row.result,
                str(row.tenant_id) if row.tenant_id else "",
                json.dumps(row.metadata, sort_keys=True, default=str),
            )
        )
        row_count += 1

    bucket = getattr(settings, "AUDIT_EXPORTS_BUCKET", "exports-gdpr")
    key = f"exports/{requested_by}/{timezone.now():%Y%m%dT%H%M%S}.csv"
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=BotoConfig(connect_timeout=5, read_timeout=30, retries={"max_attempts": 3}),
    )
    # Prepend UTF-8 BOM so Excel correctly displays accented French / Arabic
    # characters in `metadata_json`. Without it, Excel mojibakes on open.
    body = ("﻿" + buf.getvalue()).encode("utf-8")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="text/csv; charset=utf-8",
        ServerSideEncryption="AES256",
    )
    # Generate a presigned URL valid 7 days so the DPO can pull the file
    # without further authentication (Story 1.13 §AC5).
    ttl = getattr(settings, "AUDIT_EXPORT_PRESIGNED_TTL_SECONDS", 7 * 24 * 3600)
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=ttl,
    )
    log.info(
        "audit.export_csv_completed",
        key=key,
        bucket=bucket,
        row_count=row_count,
        requested_by=requested_by,
    )
    return {"key": key, "bucket": bucket, "url": url, "row_count": row_count}
