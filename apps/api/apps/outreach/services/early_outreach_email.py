"""Early-outreach transactional emails — Stories 5.5 + 5.6 + 5.7.

One function per moderation/response lifecycle event, French-only. Story 8.1:
every send goes through `apps.mailer.send_transactional` — a durable
`EmailOutbox` row is written at the call site and delivery happens
asynchronously with exponential retry; a permanently failing delivery ends as
a loud, replayable `failed` row instead of a swallowed warning. Subjects
moved from Python literals into the `*_subject.txt` templates (the outbox
rendering convention).

Outbox contexts must be JSON-serializable, so the functions flatten model
instances into plain nested dicts shaped exactly like the template lookups
(`{{ school.name }}`, `{{ outreach.id }}`, `{{ response.action }}`) — the
body templates are unchanged. Rendering happens in the mailer worker under
the project default locale (`LANGUAGE_CODE = "fr-fr"`); no template in this
family uses a locale-sensitive filter, so no pre-formatting is needed.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from apps.mailer.service import send_transactional
from apps.notifications.models import NotificationCategory
from apps.notifications.services import notify


def _site_url() -> str:
    return os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")


if TYPE_CHECKING:
    from apps.outreach.models import EarlyOutreachRequest


def _queue(*, template_base: str, to: str, context: dict[str, object]) -> None:
    send_transactional(
        template_app="outreach",
        template_base=f"email/{template_base}",
        to=to,
        context=context,
    )


def send_motivation_pending_moderation_email(*, outreach: EarlyOutreachRequest) -> None:
    _queue(
        template_base="motivation_pending_moderation",
        to=outreach.student.email,
        context={"school": {"name": outreach.school.name}},
    )


def send_motivation_approved_email(*, outreach: EarlyOutreachRequest) -> None:
    _queue(
        template_base="motivation_approved",
        to=outreach.student.email,
        context={"school": {"name": outreach.school.name}},
    )


def send_motivation_rejected_email(*, outreach: EarlyOutreachRequest, reason: str) -> None:
    _queue(
        template_base="motivation_rejected",
        to=outreach.student.email,
        context={"school": {"name": outreach.school.name}, "reason": reason},
    )


def send_outreach_expired_email(*, outreach: EarlyOutreachRequest) -> None:
    """Story 5.6 — sent when a `pending` request crosses 7 days without a
    school response and auto-transitions to `expired_7d`."""
    _queue(
        template_base="outreach_expired",
        to=outreach.student.email,
        context={"school": {"name": outreach.school.name}},
    )


#: The subject template branches on these — kept in sync with
#: `EarlyOutreachResponseAction`. The guard preserves the pre-8.1 fail-fast
#: (`_RESPONSE_SUBJECTS[response.action]` raised `KeyError` on an unknown
#: action) instead of silently rendering an empty subject line.
_RESPONSE_ACTIONS = ("interested", "not_aligned", "interview_requested")


def send_school_responded_email(*, outreach: EarlyOutreachRequest, response) -> None:
    """Story 5.7 — sent to the student the moment a school responds. The
    admission-stat point value ("+14 pts") isn't computed yet (Story 5.8's
    job) — this email is the "someone answered" signal, not the stat
    update itself.

    Story 8.4: routed through the notification ENGINE (category
    `school_responses`), not straight to the outbox — the engine applies
    the student's opt-out at the point of send and injects the legal
    footer links. An opted-out student still sees the response in-app
    (`/mes-envois`, Story 5.9): `respond_to_outreach_request` persists the
    response before this function is ever called, so the AC3 "reste
    visible in-app" guarantee is structural. The other outreach emails
    (interview slots, staff notices) stay plain transactional sends: they
    are workflow steps the student initiated, not a subscribable category.
    """
    if response.action not in _RESPONSE_ACTIONS:
        raise KeyError(response.action)
    notify(
        user_id=outreach.student.id,
        email=outreach.student.email,
        category=NotificationCategory.SCHOOL_RESPONSES,
        template_app="outreach",
        template_base="email/school_responded",
        context={
            "school": {"name": outreach.school.name},
            "outreach": {"id": outreach.id, "profession": {"name": outreach.profession.name}},
            "response": {"action": response.action, "comment": response.comment},
            "response_url": f"{_site_url()}/mes-envois/{outreach.id}",
            "explore_url": f"{_site_url()}/schools",
        },
    )


def send_interview_slot_accepted_email(*, outreach: EarlyOutreachRequest, staff_email: str) -> None:
    """Story 5.7 — sent to a school-admin email when the student accepts
    one of the proposed interview slots."""
    _queue(
        template_base="interview_slot_accepted",
        to=staff_email,
        context={"outreach": {"id": outreach.id}},
    )


def send_interview_alternative_proposed_email(
    *, outreach: EarlyOutreachRequest, staff_email: str
) -> None:
    """Story 5.7 — sent to a school-admin email when the student can't
    make any proposed slot and suggests an alternative instead."""
    _queue(
        template_base="interview_alternative_proposed",
        to=staff_email,
        context={"outreach": {"id": outreach.id}},
    )
