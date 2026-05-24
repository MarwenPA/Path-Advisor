"""GDPR Article 20 export service (Story 1.11).

Public surface (called by the DRF view):
    GdprExportService.request_export(user) -> GdprExportRequest

The Celery side (`apps.accounts.tasks`) calls the lower-level helpers:
    GdprExportService.build_export(export_id)
    GdprExportService.expire_old_exports()

Design notes:
- `request_export` is decorated with `@audit_action("gdpr.export_requested")` so
  the audit row carries the standard actor + tenant snapshot (Story 1.13).
- Dispatching the Celery task happens via `transaction.on_commit(...)` so a
  crash between row creation and broker enqueue cannot leave a pending row
  orphaned on the DB.
- The rate-limit check is two-layered: "is there an active request?" (409) is
  separate from "did you already get a ready export within 24h?" (429) — they
  surface different problems to the user.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

import boto3
import structlog
from botocore.config import Config as BotoConfig
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.gdpr_exceptions import (
    GdprExportInProgress,
    GdprExportRateLimited,
)
from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.audit.decorators import audit_action

if TYPE_CHECKING:
    from apps.accounts.models import User


log = structlog.get_logger(__name__)


class GdprExportService:
    """Stateless orchestration of GDPR exports — no instance state."""

    # ----------------------------- Public API --------------------------------

    @staticmethod
    @audit_action(
        "gdpr.export_requested",
        # On failure the decorator passes `ret=None`; resolve the subject from
        # the input kwargs in that case so we can still audit a denied attempt
        # with the right subject_id.
        subject_from=lambda kwargs, ret: (
            ret.user_id if ret is not None else getattr(kwargs.get("user"), "id", None)
        ),
        metadata_from=lambda kwargs, ret: {"export_id": ret.id} if ret is not None else {},
    )
    @transaction.atomic
    def request_export(*, user: User) -> GdprExportRequest:
        """Create a pending GdprExportRequest and schedule the build task.

        Raises:
            GdprExportInProgress: an active (pending/in_progress) export exists.
            GdprExportRateLimited: a successful export was issued within
                GDPR_EXPORT_RATE_LIMIT_HOURS — caller must retry later.
        """
        if _has_active_export(user.id):
            raise GdprExportInProgress()

        retry_after = _retry_after_seconds(user.id)
        if retry_after is not None:
            raise GdprExportRateLimited(
                detail=(
                    "Tu as déjà demandé un export il y a moins de "
                    f"{settings.GDPR_EXPORT_RATE_LIMIT_HOURS} heures. "
                    "Patiente avant d'en redemander un."
                ),
                retry_after_seconds=retry_after,
            )

        try:
            export = GdprExportRequest.objects.create(
                user_id=user.id,
                status=GdprExportStatus.PENDING,
            )
        except IntegrityError as exc:
            # Two concurrent POSTs both passed `_has_active_export` and reached
            # the INSERT. The partial unique index (migration 0004) rejects the
            # second one — translate it back into the same 409 the application
            # check would have produced (post-review patch D4, 2026-05-24).
            #
            # PostgreSQL reports the constraint name; SQLite (tests) reports the
            # column name. Match either to keep the test backend SQLite-friendly.
            message = str(exc)
            if "uniq_gdpr_active_per_user" in message or "gdpr_export_requests.user_id" in message:
                raise GdprExportInProgress() from exc
            raise

        # Local import to avoid the circular module load
        # `models → service → tasks → models` at Django startup.
        from apps.accounts.tasks import build_export

        transaction.on_commit(lambda: build_export.delay(export_id=export.id))
        return export


# --------------------------- Internal helpers ---------------------------------


def _has_active_export(user_id: str) -> bool:
    return GdprExportRequest.objects.filter(
        user_id=user_id,
        status__in=(GdprExportStatus.PENDING, GdprExportStatus.IN_PROGRESS),
    ).exists()


def _retry_after_seconds(user_id: str) -> int | None:
    """Return remaining seconds in the rate-limit window, or None if free.

    Only `ready` exports count toward the quota — a `failed` attempt leaves
    the slot open so the user can retry immediately (story §AC2).
    """
    window = timedelta(hours=settings.GDPR_EXPORT_RATE_LIMIT_HOURS)
    cutoff = timezone.now() - window
    last_ready = (
        GdprExportRequest.objects.filter(
            user_id=user_id,
            status=GdprExportStatus.READY,
            ready_at__gte=cutoff,
        )
        .order_by("-ready_at")
        .first()
    )
    if last_ready is None or last_ready.ready_at is None:
        return None
    remaining = (last_ready.ready_at + window) - timezone.now()
    return max(0, int(remaining.total_seconds()))


def gdpr_s3_client() -> Any:
    """Return a boto3 S3 client wired with the project's MinIO/Scaleway creds.

    Mirrors `apps.audit.services.archive_service._s3_client` rather than
    importing it — Story 1.11 §3.1 deliberately duplicates this factory to
    avoid a premature cross-app refactor. Both versions converge once the
    third caller appears.
    """
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=BotoConfig(
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 3},
        ),
    )
