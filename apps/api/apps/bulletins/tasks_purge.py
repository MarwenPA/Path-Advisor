"""Celery beat task — purge expired unvalidated bulletins (Story 2.3 T3, RGPD).

Runs daily. Deletes bulletins where `expires_at < now() AND validated_at IS NULL`.
Each deleted bulletin's S3 file is also removed.

The 30-day retention window is set at `Bulletin.save()` time via `expires_at`.
"""

from __future__ import annotations

import logging

import boto3
from botocore.config import Config
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.bulletins.models import Bulletin

log = logging.getLogger(__name__)


@shared_task(name="bulletins.purge_expired")
def purge_expired_bulletins() -> dict:
    """Delete expired unvalidated bulletins from DB + S3."""
    expired_qs = Bulletin.objects.filter(
        expires_at__lt=timezone.now(),
        validated_at__isnull=True,
    )

    count = expired_qs.count()
    if count == 0:
        return {"purged": 0}

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )
    bucket = settings.BULLETINS_BUCKET
    purged = 0
    failed = 0

    if not getattr(settings, "USE_TZ", False):
        log.error("purge_expired_bulletins requires USE_TZ=True — aborting to prevent DST drift")
        return {"purged": 0, "error": "USE_TZ must be True"}

    for bulletin in expired_qs.iterator():
        try:
            # Delete DB row first — S3 orphan is recoverable via lifecycle policy;
            # a retained DB row pointing to a deleted S3 object is not.
            bulletin.delete()
            s3.delete_object(Bucket=bucket, Key=bulletin.file_path)
            purged += 1
        except Exception as exc:
            log.error(
                "Failed to purge bulletin %s (key=%s): %s",
                bulletin.id,
                bulletin.file_path,
                exc,
            )
            failed += 1

    log.info("Bulletin purge complete: purged=%d, failed=%d", purged, failed)
    return {"purged": purged, "failed": failed}
