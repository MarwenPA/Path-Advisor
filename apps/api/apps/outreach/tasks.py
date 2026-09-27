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


@shared_task(name="outreach.send_interview_reminders")
def send_interview_reminders() -> dict:
    """Story 10.4 — rappels J-1 et H-1 des RDV visio (beat toutes les 15 min).

    Fenêtres balayées plutôt qu'ETA : le broker Redis a un
    `visibility_timeout` de 4 h — un ETA à J-1 serait redélivré et
    enverrait deux fois. Chaque rappel se réclame par UPDATE conditionnel
    (patron milestone 8.3) : exactement-une-fois même avec deux workers.
    Un RDV déjà commencé ne rappelle plus rien (mieux vaut un silence
    qu'un buzz en plein entretien).
    """
    from apps.outreach.models import InterviewMeeting
    from apps.outreach.services.early_outreach_email import send_interview_reminder_email

    now = timezone.now()
    sent = {"24h": 0, "1h": 0}

    with bypass_rls(reason="outreach.send_interview_reminders"):
        for horizon, delta, claim_field in (
            ("24h", timedelta(hours=24), "reminder_24h_sent_at"),
            ("1h", timedelta(hours=1), "reminder_1h_sent_at"),
        ):
            due = list(
                InterviewMeeting.objects.filter(
                    scheduled_at__gt=now,
                    scheduled_at__lte=now + delta,
                    **{f"{claim_field}__isnull": True},
                ).select_related("outreach__student", "outreach__school")
            )
            for meeting in due:
                claimed = InterviewMeeting.objects.filter(
                    pk=meeting.pk, **{f"{claim_field}__isnull": True}
                ).update(**{claim_field: now})
                if not claimed:
                    continue
                try:
                    send_interview_reminder_email(
                        outreach=meeting.outreach, meeting=meeting, horizon=horizon
                    )
                    sent[horizon] += 1
                except Exception:
                    logger.warning(
                        "outreach.interview_reminder.notify_failed",
                        extra={"meeting_id": meeting.pk, "horizon": horizon},
                        exc_info=True,
                    )

    if sent["24h"] or sent["1h"]:
        logger.info("outreach.interview_reminders_sent", extra=sent)
    return sent
