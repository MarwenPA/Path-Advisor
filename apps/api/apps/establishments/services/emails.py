"""Email dispatch for the establishments app — Story 6.5 §T6.

Mirrors `apps.family.services.emails` — same best-effort send contract (SMTP
failure never breaks the transaction that triggered it).
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
    subject = render_to_string(f"establishments/{template_base}_subject.txt", context).strip()
    body_txt = render_to_string(f"establishments/{template_base}.txt", context)
    body_html = render_to_string(f"establishments/{template_base}.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send(fail_silently=False)
        log.info("establishments.email_sent", template=template_base, to=to)
        return True
    except Exception as exc:
        log.warning("establishments.email_failed", template=template_base, to=to, error=str(exc))
        return False


def send_counselor_invitation(invitation) -> bool:
    invitation_url = f"{_site_url()}/auth/invitation-conseillere/{invitation.token}"
    return _send(
        template_base="counselor_invitation",
        to=invitation.email,
        context={
            "establishment_name": invitation.establishment.name,
            "invitation_url": invitation_url,
        },
    )


def send_student_import_invitation(invitation) -> bool:
    invitation_url = f"{_site_url()}/auth/invitation-eleve/{invitation.token}"
    return _send(
        template_base="student_import_invitation",
        to=invitation.user.email,
        context={
            "establishment_name": invitation.cohort.establishment.name,
            "invitation_url": invitation_url,
        },
    )
