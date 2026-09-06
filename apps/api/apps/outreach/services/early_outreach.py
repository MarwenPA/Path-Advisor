"""Early-outreach request service — Story 5.4 (AC2, AC3)."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from apps.audit.decorators import audit_action
from apps.outreach.exceptions import MonthlyOutreachQuotaExceeded
from apps.outreach.models import EarlyOutreachRequest
from apps.professions.models import Profession
from apps.schools.models import Parcours, School

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
    """AC2 — create a `pending` request. Caller (the view) is responsible for
    the `IsPremium` permission check (AC5) — this service assumes it already
    passed, so it can also be called from a management command/shell without
    re-deriving the permission logic.
    """
    if count_outreach_this_month(student=student) >= MONTHLY_QUOTA:
        raise MonthlyOutreachQuotaExceeded()

    parcours = _resolve_default_parcours(profession=profession, school=school)
    return EarlyOutreachRequest.objects.create(
        student=student,
        school=school,
        profession=profession,
        parcours=parcours,
        motivation_text=motivation_text,
    )
