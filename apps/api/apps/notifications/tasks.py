"""Story 8.3 — daily Parcoursup-calendar dispatch (beat).

One batch per milestone, exactly once: `notified_at` is set inside the same
transaction that creates the outbox rows — a crash before commit sends
nothing and marks nothing; after commit, every email is durably queued
(8.1) and per-user opt-out was already honoured by the engine (8.2).

Cross-user audience read runs under `with_system_actor` — the documented
escape hatch for beat tasks that act on behalf of the platform (see
`core/rls.py`; distinct from an anonymous bypass for forensics).
"""

from __future__ import annotations

import os
from datetime import timedelta

import structlog
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.utils.formats import date_format

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import with_system_actor

from .milestone_copy import MILESTONE_COPY
from .models import MilestoneKind, NotificationCategory, ParcoursupMilestone
from .services import notify

log = structlog.get_logger(__name__)

#: Story 8.3 audience: élèves in Terminale or post-bac (AC1).
AUDIENCE_LEVELS = ("lycee_terminale", "postbac")


def _site_url() -> str:
    return os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")


@shared_task(name="notifications.send_parcoursup_milestone_notifications")
def send_parcoursup_milestone_notifications() -> int:
    """Send every due, un-notified milestone. Returns emails queued."""
    today = timezone.localdate()
    queued = 0

    with with_system_actor(reason="notifications.parcoursup_calendar_beat"):
        due = list(ParcoursupMilestone.objects.filter(notified_at__isnull=True).order_by("date"))
        due = [m for m in due if (m.date - timedelta(days=m.notify_days_before)) <= today]

        for milestone in due:
            copy = MILESTONE_COPY[MilestoneKind(milestone.kind)]
            date_fr = date_format(milestone.date, "j F Y")
            recipients = list(
                User.objects.filter(
                    role=UserRole.STUDENT,
                    status=UserStatus.ACTIVE,
                    email_verified_at__isnull=False,
                    # `level` lives on the LevelProfile ONE-TO-ONE hanging off
                    # StudentProfile (related_name chain verified in
                    # students/models.py — a naive student_profile__level
                    # would silently match nobody).
                    student_profile__level_profile__level__in=AUDIENCE_LEVELS,
                ).values_list("id", "email")
            )

            with transaction.atomic():
                for user_id, email in recipients:
                    row = notify(
                        user_id=user_id,
                        email=email,
                        category=NotificationCategory.PARCOURSUP_CALENDAR,
                        template_app="notifications",
                        template_base="email/parcoursup_milestone",
                        context={
                            "subject": str(copy["subject"]).format(date=date_fr),
                            "intro": str(copy["intro"]).format(date=date_fr),
                            "checklist": copy["checklist"],
                            "cta_label": copy["cta_label"],
                            "cta_url": f"{_site_url()}{copy['cta_path']}",
                        },
                    )
                    if row is not None:
                        queued += 1
                milestone.notified_at = timezone.now()
                milestone.save(update_fields=["notified_at"])

            log.info(
                "notifications.parcoursup_milestone_dispatched",
                kind=milestone.kind,
                campaign=milestone.campaign,
                recipients=len(recipients),
                queued=queued,
            )

    return queued
