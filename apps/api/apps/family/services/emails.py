"""Email dispatch helpers for the parent-invitation flow (Story 6.1 §T4).

Mirrors `apps.accounts.services.parental_consent_email` — same best-effort
send contract (SMTP failure never breaks the transaction that triggered it).
"""

from __future__ import annotations

import os

import structlog
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

log = structlog.get_logger(__name__)


def _site_url() -> str:
    site_url = os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")
    return site_url.rstrip("/")


def _send(*, template_base: str, to: str, context: dict[str, object]) -> bool:
    subject = render_to_string(f"family/{template_base}_subject.txt", context).strip()
    body_txt = render_to_string(f"family/{template_base}.txt", context)
    body_html = render_to_string(f"family/{template_base}.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send(fail_silently=False)
        log.info("family.email_sent", template=template_base, to=to)
        return True
    except Exception as exc:
        log.warning("family.email_failed", template=template_base, to=to, error=str(exc))
        return False


def send_invitation_to_parent(invitation) -> bool:
    invitation_url = f"{_site_url()}/auth/invitation-parent/{invitation.token}"
    return _send(
        template_base="parent_invitation",
        to=invitation.parent_email,
        context={
            "student_first_name": invitation.student.email.split("@")[0],
            "custom_message": invitation.custom_message,
            "invitation_url": invitation_url,
        },
    )


def send_invitation_accepted_to_student(invitation, parent) -> bool:
    return _send(
        template_base="parent_invitation_accepted_to_student",
        to=invitation.student.email,
        context={
            "student_first_name": invitation.student.email.split("@")[0],
            "parent_first_name": parent.email.split("@")[0],
        },
    )


def send_parent_link_revoked_to_parent(link) -> bool:
    return _send(
        template_base="parent_link_revoked_to_parent",
        to=link.parent.email,
        context={"student_first_name": link.student.email.split("@")[0]},
    )
