"""Early-outreach transactional emails — Stories 5.5 + 5.6 + 5.7.

Three templates, one per moderation transition, mirroring the
`apps.accounts.services.account_deletion_email` pattern (`_send` helper +
one function per lifecycle event, French-only, `fr-FR` locale override so
date filters render French month names):

    - `motivation_pending_moderation.{txt,html}` — sent right after
      submission, when `motivation_text` is non-empty (AC: "en cours de
      relecture, sous 24h ouvrées").
    - `motivation_approved.{txt,html}` — sent when a path_admin approves.
    - `motivation_rejected.{txt,html}` — sent when a path_admin rejects,
      includes the `reason` so the student can correct and resubmit.

All three are best-effort from the caller's point of view — the service
functions in `early_outreach.py` wrap these calls in try/except (SMTP
failure must never roll back a moderation decision that's already been
persisted).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

if TYPE_CHECKING:
    from apps.outreach.models import EarlyOutreachRequest


def _send(*, subject: str, template: str, to: str, context: dict) -> None:
    with translation.override("fr-FR"):
        html_body = render_to_string(f"{template}.html", context)
        text_body = render_to_string(f"{template}.txt", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


def send_motivation_pending_moderation_email(*, outreach: EarlyOutreachRequest) -> None:
    _send(
        subject="[Path-Advisor] Ta motivation est en cours de relecture",
        template="outreach/email/motivation_pending_moderation",
        to=outreach.student.email,
        context={"outreach": outreach, "school": outreach.school},
    )


def send_motivation_approved_email(*, outreach: EarlyOutreachRequest) -> None:
    _send(
        subject="[Path-Advisor] Ton profil est en route vers l'école",
        template="outreach/email/motivation_approved",
        to=outreach.student.email,
        context={"outreach": outreach, "school": outreach.school},
    )


def send_motivation_rejected_email(*, outreach: EarlyOutreachRequest, reason: str) -> None:
    _send(
        subject="[Path-Advisor] Ta motivation nécessite une correction",
        template="outreach/email/motivation_rejected",
        to=outreach.student.email,
        context={"outreach": outreach, "school": outreach.school, "reason": reason},
    )


def send_outreach_expired_email(*, outreach: EarlyOutreachRequest) -> None:
    """Story 5.6 — sent when a `pending` request crosses 7 days without a
    school response and auto-transitions to `expired_7d`."""
    _send(
        subject="[Path-Advisor] Pas de réponse de l'école — ta stat est inchangée",
        template="outreach/email/outreach_expired",
        to=outreach.student.email,
        context={"outreach": outreach, "school": outreach.school},
    )


_RESPONSE_SUBJECTS = {
    "interested": "[Path-Advisor] {school} a répondu — profil intéressant !",
    "not_aligned": "[Path-Advisor] {school} a répondu à ton envoi",
    "interview_requested": "[Path-Advisor] {school} te propose un entretien",
}


def send_school_responded_email(*, outreach: EarlyOutreachRequest, response) -> None:
    """Story 5.7 — sent to the student the moment a school responds. The
    admission-stat point value ("+14 pts") isn't computed yet (Story 5.8's
    job) — this email is the "someone answered" signal, not the stat
    update itself."""
    _send(
        subject=_RESPONSE_SUBJECTS[response.action].format(school=outreach.school.name),
        template="outreach/email/school_responded",
        to=outreach.student.email,
        context={"outreach": outreach, "school": outreach.school, "response": response},
    )


def send_interview_slot_accepted_email(*, outreach: EarlyOutreachRequest, staff_email: str) -> None:
    """Story 5.7 — sent to a school-admin email when the student accepts
    one of the proposed interview slots."""
    _send(
        subject="[Path-Advisor] Créneau d'entretien accepté",
        template="outreach/email/interview_slot_accepted",
        to=staff_email,
        context={"outreach": outreach},
    )


def send_interview_alternative_proposed_email(
    *, outreach: EarlyOutreachRequest, staff_email: str
) -> None:
    """Story 5.7 — sent to a school-admin email when the student can't
    make any proposed slot and suggests an alternative instead."""
    _send(
        subject="[Path-Advisor] L'élève propose un autre créneau",
        template="outreach/email/interview_alternative_proposed",
        to=staff_email,
        context={"outreach": outreach},
    )
