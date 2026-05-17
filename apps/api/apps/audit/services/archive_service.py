"""Monthly S3 archival of audit entries older than the retention horizon.

Volume MVP is small enough that we KEEP rows in the table after archival —
no DELETE attempt (the trigger would block it anyway). Story 1.13 §AC6
documents the rationale.

A dedicated boto3 client (not `default_storage` / django-storages) keeps the
audit bucket isolated from user-facing media — see Story 1.13 §Anti-patterns.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from dataclasses import asdict, dataclass
from datetime import UTC, timedelta
from typing import Any

import boto3
from django.conf import settings
from django.utils import timezone

from apps.audit.models import AuditLog


@dataclass
class ArchiveManifest:
    first_id: str
    last_id: str
    first_created_at: str
    last_created_at: str
    row_count: int
    first_hash: str
    last_hash: str
    sha256_of_archive: str
    archive_key: str
    manifest_key: str


def _s3_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


def archive_logs_older_than(days: int) -> ArchiveManifest | None:
    """Stream entries older than `days` to S3 as one gzipped JSONL + manifest."""
    # Single clock read for both the cutoff and the S3 key path so a midnight
    # UTC crossing during the task body can't desynchronise them.
    now = timezone.now().astimezone(UTC)
    cutoff = now - timedelta(days=days)
    qs = AuditLog.objects.filter(created_at__lt=cutoff).order_by("created_at")
    if not qs.exists():
        return None

    bucket = settings.AUDIT_ARCHIVE_BUCKET
    archive_key = f"archive/{now:%Y/%m}/audit-logs-{now:%Y%m}.jsonl.gz"
    manifest_key = f"archive/{now:%Y/%m}/manifest.json"

    buf = io.BytesIO()
    sha = hashlib.sha256()
    first_row = None
    last_row = None
    row_count = 0

    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        for row in qs.iterator(chunk_size=500):
            if first_row is None:
                first_row = row
            last_row = row
            line = (
                json.dumps(_row_to_dict(row), sort_keys=True, default=str).encode("utf-8") + b"\n"
            )
            gz.write(line)
            sha.update(line)
            row_count += 1

    if first_row is None or last_row is None:
        return None

    body = buf.getvalue()
    s3 = _s3_client()
    s3.put_object(
        Bucket=bucket,
        Key=archive_key,
        Body=body,
        # The body is JSONL gzipped — express both layers so downstream tooling
        # can choose to either request decompressed content (`Accept-Encoding`)
        # or stream as-is.
        ContentType="application/x-ndjson",
        ContentEncoding="gzip",
        ServerSideEncryption="AES256",
    )

    manifest = ArchiveManifest(
        first_id=first_row.id,
        last_id=last_row.id,
        first_created_at=first_row.created_at.isoformat(),
        last_created_at=last_row.created_at.isoformat(),
        row_count=row_count,
        first_hash=first_row.row_hash,
        last_hash=last_row.row_hash,
        sha256_of_archive=sha.hexdigest(),
        archive_key=archive_key,
        manifest_key=manifest_key,
    )
    s3.put_object(
        Bucket=bucket,
        Key=manifest_key,
        Body=json.dumps(asdict(manifest), sort_keys=True).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    return manifest


def _row_to_dict(row: AuditLog) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "actor_id": row.actor_id,
        "actor_role": row.actor_role,
        "tenant_id": str(row.tenant_id) if row.tenant_id else None,
        "subject_id": row.subject_id,
        "action": row.action,
        "result": row.result,
        "request_id": row.request_id,
        "ip_address_hash": row.ip_address_hash,
        "user_agent": row.user_agent,
        "metadata": row.metadata,
        "prev_hash": row.prev_hash,
        "row_hash": row.row_hash,
    }
