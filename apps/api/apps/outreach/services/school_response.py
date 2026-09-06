"""School response to an early-outreach request — Story 5.7.

Two directions:
    - `respond_to_outreach_request` — the school's one-shot answer (one of
      the 3 actions). Flips the request to `responded`.
    - `accept_interview_slot` / `propose_interview_alternative` — the
      student's reply when the action was `interview_requested`. Single
      round only (§2 scope decision, see `EarlyOutreachResponse`'s
      docstring) — no multi-round negotiation loop in the MVP.

Story 5.8 propagates the response to the student's admission stat
(`AdmissionPredictionService.apply_outreach_response_delta`) synchronously,
in the same call — trivially satisfies the "< 5 minutes" NFR-P5 without a
separate queue/worker for the MVP volume.
"""

from __future__ import annotations

import logging

from apps.audit.decorators import audit_action
from apps.core.rls import bypass_rls
from apps.outreach.exceptions import (
    InterviewSlotNotProposed,
    NoInterviewToRespondTo,
    OutreachAlreadyResponded,
)
from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachRequestStatus,
    EarlyOutreachResponse,
    EarlyOutreachResponseAction,
)
from apps.outreach.services.early_outreach_email import (
    send_interview_alternative_proposed_email,
    send_interview_slot_accepted_email,
    send_school_responded_email,
)
from apps.schools.models import SchoolStaff
from apps.schools.services import AdmissionPredictionService

logger = logging.getLogger(__name__)


@audit_action(
    "early_outreach.school_responded",
    subject_from=lambda kwargs, ret: ret.request_id if ret else None,
    metadata_from=lambda kwargs, ret: {"action": kwargs["action"]},
)
def respond_to_outreach_request(
    *,
    outreach: EarlyOutreachRequest,
    action: str,
    comment: str = "",
    proposed_slots: list[str] | None = None,
) -> EarlyOutreachResponse:
    """AC — the school's one-shot response. `outreach` must be `pending`
    (caller already scoped it to the school via `school_reception`).
    `proposed_slots` is only meaningful for `interview_requested` —
    the serializer enforces 2-3 entries for that action, empty otherwise.
    """
    if outreach.status != EarlyOutreachRequestStatus.PENDING:
        raise OutreachAlreadyResponded()

    response = EarlyOutreachResponse.objects.create(
        request=outreach,
        action=action,
        comment=comment,
        proposed_slots=proposed_slots or [],
    )
    outreach.status = EarlyOutreachRequestStatus.RESPONDED
    outreach.save(update_fields=["status", "updated_at"])

    # Story 5.8 AC — recompute the student's admission stat for this school
    # right away. A failure here must not roll back the response itself
    # (the school's answer is the source of truth; the stat is derived).
    try:
        AdmissionPredictionService().apply_outreach_response_delta(
            school=outreach.school, user=outreach.student, action=action
        )
    except Exception:
        logger.warning(
            "outreach.stat_propagation_failed",
            extra={"outreach_id": outreach.id},
            exc_info=True,
        )

    try:
        send_school_responded_email(outreach=outreach, response=response)
    except Exception:
        logger.warning(
            "outreach.school_responded.notify_failed",
            extra={"outreach_id": outreach.id},
            exc_info=True,
        )
    return response


def _notify_school_staff(outreach: EarlyOutreachRequest, *, kind: str) -> None:
    """Best-effort fan-out to every `SchoolStaff` linked to the request's
    school — in the MVP that's usually one person, but nothing enforces
    it.

    Called from a student-scoped request (RLS identity = the student), so
    reading another user's (the school staff's) email needs `bypass_rls` —
    same rationale as `school_reception.py`: the authorization is "this
    school owns this request", not the RLS policy.
    """
    with bypass_rls(reason="school_response.notify_school_staff"):
        emails = list(
            SchoolStaff.objects.filter(school_id=outreach.school_id).values_list(
                "user__email", flat=True
            )
        )
    for email in emails:
        try:
            if kind == "accepted":
                send_interview_slot_accepted_email(outreach=outreach, staff_email=email)
            else:
                send_interview_alternative_proposed_email(outreach=outreach, staff_email=email)
        except Exception:
            logger.warning(
                f"outreach.interview_{kind}.notify_failed",
                extra={"outreach_id": outreach.id, "staff_email": email},
                exc_info=True,
            )


@audit_action(
    "early_outreach.interview_slot_accepted",
    subject_from=lambda kwargs, ret: ret.request_id if ret else None,
    metadata_from=lambda kwargs, ret: {},
)
def accept_interview_slot(*, outreach: EarlyOutreachRequest, slot: str) -> EarlyOutreachResponse:
    """Student accepts one of the school's proposed slots. `outreach` must
    already have an `interview_requested` response with no prior decision
    (`accepted_slot`/`alternative_note` both empty) — caller scopes
    `outreach` to `student=request.user`."""
    response = getattr(outreach, "response", None)
    if (
        response is None
        or response.action != EarlyOutreachResponseAction.INTERVIEW_REQUESTED
        or response.accepted_slot
        or response.alternative_note
    ):
        raise NoInterviewToRespondTo()
    if slot not in response.proposed_slots:
        raise InterviewSlotNotProposed()

    response.accepted_slot = slot
    response.save(update_fields=["accepted_slot", "updated_at"])
    _notify_school_staff(outreach, kind="accepted")
    return response


@audit_action(
    "early_outreach.interview_alternative_proposed",
    subject_from=lambda kwargs, ret: ret.request_id if ret else None,
    metadata_from=lambda kwargs, ret: {},
)
def propose_interview_alternative(
    *, outreach: EarlyOutreachRequest, note: str
) -> EarlyOutreachResponse:
    """Student can't make any proposed slot and suggests an alternative in
    free text — the school follows up externally (§2 scope decision, no
    2nd negotiation round in the MVP)."""
    response = getattr(outreach, "response", None)
    if (
        response is None
        or response.action != EarlyOutreachResponseAction.INTERVIEW_REQUESTED
        or response.accepted_slot
        or response.alternative_note
    ):
        raise NoInterviewToRespondTo()

    response.alternative_note = note
    response.save(update_fields=["alternative_note", "updated_at"])
    _notify_school_staff(outreach, kind="alternative")
    return response
