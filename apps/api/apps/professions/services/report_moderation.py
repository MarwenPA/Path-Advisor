"""Story 9.3 — the report-moderation workflow.

Every transition writes `handled_by`/`handled_at` + an audit row in the
same transaction, and (resolve / request-info) notifies the reporter
through the 8.2 engine — category `report_updates`, so opt-out and the
legal footer are enforced by construction. `dismissed` sends NOTHING
(story doc §2.4: a rejection notified without a reply channel frustrates
more than it informs; the reason stays queryable for support).
"""

from __future__ import annotations

import structlog
from django.db import transaction
from django.utils import timezone

from apps.audit.decorators import record_audit
from apps.notifications.models import NotificationCategory
from apps.notifications.services import notify

from ..models import ProfessionReport

log = structlog.get_logger(__name__)


def _site_url() -> str:
    import os

    return os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")


def _transition(report: ProfessionReport, *, status: str, editor, note: str) -> None:
    report.status = status
    report.admin_note = note
    report.handled_by = editor
    report.handled_at = timezone.now()
    report.save(update_fields=["status", "admin_note", "handled_by", "handled_at"])


def resolve_report(*, report: ProfessionReport, editor, note: str = "") -> ProfessionReport:
    with transaction.atomic():
        _transition(report, status=ProfessionReport.Status.RESOLVED, editor=editor, note=note)
        record_audit(
            action="moderation.report_resolved",
            result="success",
            actor=editor,
            subject_id=report.pk,
            metadata={"profession": report.profession.slug},
        )
        if report.reporter_id:
            notify(
                user_id=report.reporter_id,
                email=report.reporter.email,
                category=NotificationCategory.REPORT_UPDATES,
                template_app="notifications",
                template_base="email/report_resolved",
                context={
                    "profession_name": report.profession.name,
                    "fiche_url": f"{_site_url()}/metiers/{report.profession.slug}",
                },
            )
    return report


def dismiss_report(*, report: ProfessionReport, editor, reason: str) -> ProfessionReport:
    if not reason.strip():
        raise ValueError("Un motif de rejet est obligatoire.")
    with transaction.atomic():
        _transition(
            report, status=ProfessionReport.Status.DISMISSED, editor=editor, note=reason.strip()
        )
        record_audit(
            action="moderation.report_dismissed",
            result="success",
            actor=editor,
            subject_id=report.pk,
            metadata={"profession": report.profession.slug, "reason": reason.strip()[:200]},
        )
    return report


def request_report_info(*, report: ProfessionReport, editor, message: str) -> ProfessionReport:
    if not message.strip():
        raise ValueError("Un message pour l'élève est obligatoire.")
    with transaction.atomic():
        _transition(
            report,
            status=ProfessionReport.Status.INFO_REQUESTED,
            editor=editor,
            note=message.strip(),
        )
        record_audit(
            action="moderation.report_info_requested",
            result="success",
            actor=editor,
            subject_id=report.pk,
            metadata={"profession": report.profession.slug},
        )
        if report.reporter_id:
            notify(
                user_id=report.reporter_id,
                email=report.reporter.email,
                category=NotificationCategory.REPORT_UPDATES,
                template_app="notifications",
                template_base="email/report_info_requested",
                context={
                    "profession_name": report.profession.name,
                    "admin_message": message.strip(),
                    "fiche_url": f"{_site_url()}/metiers/{report.profession.slug}",
                },
            )
    return report
