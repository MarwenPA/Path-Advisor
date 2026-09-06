"""Celery beat task — Story 5.6 AC ("un envoi reçu il y a > 7 jours sans
réponse bascule à `expired_7d`, l'élève reçoit une notification, l'école
ne peut plus répondre").

Registered in `path_advisor/celery.py`'s `beat_schedule`.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.rls import bypass_rls
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachRequestStatus
from apps.outreach.services.early_outreach_email import send_outreach_expired_email

logger = logging.getLogger(__name__)

EXPIRY_DAYS = 7


@shared_task(name="outreach.expire_stale_requests")
def expire_stale_early_outreach_requests() -> int:
    """Only `pending` requests can go stale — a request stuck in
    `pending_moderation`/`rejected` was never actually visible to the
    school, so its clock hasn't started (Story 5.5 owns unblocking those)."""
    cutoff = timezone.now() - timedelta(days=EXPIRY_DAYS)

    # A Celery beat run has no request/RLS identity — same rationale as
    # `SubscriptionService.process_dunning`'s `bypass_rls(reason="billing.
    # dunning")`: this is a legitimate system-level job reading across
    # students, not a per-request session.
    with bypass_rls(reason="outreach.expire_stale_requests"):
        stale = list(
            EarlyOutreachRequest.objects.filter(
                status=EarlyOutreachRequestStatus.PENDING, created_at__lt=cutoff
            ).select_related("school", "student")
        )

        expired_count = 0
        for outreach in stale:
            outreach.status = EarlyOutreachRequestStatus.EXPIRED_7D
            outreach.save(update_fields=["status", "updated_at"])
            expired_count += 1
            try:
                send_outreach_expired_email(outreach=outreach)
            except Exception:
                logger.warning(
                    "outreach.expired.notify_failed",
                    extra={"outreach_id": outreach.id},
                    exc_info=True,
                )
    return expired_count
