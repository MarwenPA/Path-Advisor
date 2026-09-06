"""Early-outreach request service — Stories 5.4 (AC2, AC3) + 5.5 (moderation)."""

from __future__ import annotations

import logging
from datetime import datetime

from django.utils import timezone

from apps.audit.decorators import audit_action
from apps.outreach.exceptions import MonthlyOutreachQuotaExceeded, OutreachModerationStateError
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachRequestStatus
from apps.outreach.services.early_outreach_email import (
    send_motivation_approved_email,
    send_motivation_pending_moderation_email,
    send_motivation_rejected_email,
)
from apps.professions.models import Profession
from apps.schools.models import Parcours, School

logger = logging.getLogger(__name__)

MONTHLY_QUOTA = 5


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def count_outreach_this_month(*, student) -> int:
    """AC3 — 5 envois / mois civil / élève, recompté à chaque appel (pas de
    table de quota séparée — volume MVP trop faible pour le justifier)."""
    now = timezone.now()
    return EarlyOutreachRequest.objects.filter(
        student=student, created_at__gte=_month_start(now)
    ).count()


def _resolve_default_parcours(*, profession: Profession, school: School) -> Parcours | None:
    """§2 scope decision — no manual parcours picker in the Sheet; resolve
    the `is_default=True` Parcours for (profession, target_school=school)
    if one exists, else leave `null`."""
    return Parcours.objects.filter(
        profession=profession, target_school=school, is_default=True
    ).first()


@audit_action(
    "early_outreach.created",
    subject_from=lambda kwargs, ret: ret.id if ret else None,
    metadata_from=lambda kwargs, ret: {
        "school_id": str(kwargs["school"].id),
        "profession_id": kwargs["profession"].id,
        "has_motivation": bool(kwargs.get("motivation_text")),
    },
)
def create_early_outreach_request(
    *, student, school: School, profession: Profession, motivation_text: str = ""
) -> EarlyOutreachRequest:
    """AC2 — create a request. Caller (the view) is responsible for the
    `IsPremium` permission check (AC5) — this service assumes it already
    passed, so it can also be called from a management command/shell without
    re-deriving the permission logic.

    Story 5.5 — a non-empty `motivation_text` gates the request into
    `pending_moderation` (blocked until a path_admin reviews it) instead of
    `pending`. Word-count validation (200-500) is the serializer's job, not
    this service's — it must also run when re-validating from a shell.
    """
    if count_outreach_this_month(student=student) >= MONTHLY_QUOTA:
        raise MonthlyOutreachQuotaExceeded()

    parcours = _resolve_default_parcours(profession=profession, school=school)
    has_motivation = bool(motivation_text.strip())
    outreach = EarlyOutreachRequest.objects.create(
        student=student,
        school=school,
        profession=profession,
        parcours=parcours,
        motivation_text=motivation_text,
        status=(
            EarlyOutreachRequestStatus.PENDING_MODERATION
            if has_motivation
            else EarlyOutreachRequestStatus.PENDING
        ),
    )
    if has_motivation:
        try:
            send_motivation_pending_moderation_email(outreach=outreach)
        except Exception:
            logger.warning(
                "outreach.motivation_pending_moderation.notify_failed",
                extra={"outreach_id": outreach.id},
                exc_info=True,
            )
    return outreach


@audit_action(
    "early_outreach.motivation_approved",
    subject_from=lambda kwargs, ret: ret.id if ret else None,
    metadata_from=lambda kwargs, ret: {"actor_role": "path_admin"},
)
def approve_early_outreach_motivation(*, outreach: EarlyOutreachRequest) -> EarlyOutreachRequest:
    """Story 5.5 — approve a `pending_moderation` request: unblocks it (back
    to `pending`, now visible/sendable to the school) and notifies the
    student. Raises `OutreachModerationStateError` if it isn't currently
    `pending_moderation` (e.g. already approved, or never had a motivation).

    Caller (view/admin action) is responsible for fetching `outreach` (and
    for the `IsPathAdmin` permission check) — this service assumes both
    already happened.
    """
    if outreach.status != EarlyOutreachRequestStatus.PENDING_MODERATION:
        raise OutreachModerationStateError()

    outreach.status = EarlyOutreachRequestStatus.PENDING
    outreach.rejection_reason = ""
    outreach.save(update_fields=["status", "rejection_reason", "updated_at"])
    try:
        send_motivation_approved_email(outreach=outreach)
    except Exception:
        logger.warning(
            "outreach.motivation_approved.notify_failed",
            extra={"outreach_id": outreach.id},
            exc_info=True,
        )
    return outreach


@audit_action(
    "early_outreach.motivation_rejected",
    subject_from=lambda kwargs, ret: ret.id if ret else None,
    metadata_from=lambda kwargs, ret: {"actor_role": "path_admin"},
)
def reject_early_outreach_motivation(
    *, outreach: EarlyOutreachRequest, reason: str
) -> EarlyOutreachRequest:
    """Story 5.5 — reject a `pending_moderation` request: stays blocked,
    `rejection_reason` recorded, student notified with the reason and the
    ability to correct + resubmit."""
    if outreach.status != EarlyOutreachRequestStatus.PENDING_MODERATION:
        raise OutreachModerationStateError()

    outreach.status = EarlyOutreachRequestStatus.REJECTED
    outreach.rejection_reason = reason
    outreach.save(update_fields=["status", "rejection_reason", "updated_at"])
    try:
        send_motivation_rejected_email(outreach=outreach, reason=reason)
    except Exception:
        logger.warning(
            "outreach.motivation_rejected.notify_failed",
            extra={"outreach_id": outreach.id},
            exc_info=True,
        )
    return outreach


@audit_action(
    "early_outreach.motivation_resubmitted",
    subject_from=lambda kwargs, ret: ret.id if ret else None,
    metadata_from=lambda kwargs, ret: {},
)
def resubmit_early_outreach_motivation(
    *, outreach: EarlyOutreachRequest, motivation_text: str
) -> EarlyOutreachRequest:
    """Story 5.5 — a student corrects and resubmits a `rejected` motivation.
    Goes back to `pending_moderation`. Caller (the view) is responsible for
    scoping `outreach` to the requesting student — a student must never
    resubmit someone else's request."""
    if outreach.status != EarlyOutreachRequestStatus.REJECTED:
        raise OutreachModerationStateError()

    outreach.motivation_text = motivation_text
    outreach.status = EarlyOutreachRequestStatus.PENDING_MODERATION
    outreach.rejection_reason = ""
    outreach.save(update_fields=["motivation_text", "status", "rejection_reason", "updated_at"])
    try:
        send_motivation_pending_moderation_email(outreach=outreach)
    except Exception:
        logger.warning(
            "outreach.motivation_resubmitted.notify_failed",
            extra={"outreach_id": outreach.id},
            exc_info=True,
        )
    return outreach
