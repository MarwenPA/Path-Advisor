"""Early-outreach moderation transactional emails — Story 5.5.

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
