"""Email dispatch for billing — Story 5.3 §T5.

Mirrors `apps.family.services.emails` — same best-effort send contract
(SMTP failure never breaks the webhook transaction that triggered it).
"""

from __future__ import annotations

import structlog
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

log = structlog.get_logger(__name__)


def _send(*, template_base: str, to: str, context: dict[str, object]) -> bool:
    subject = render_to_string(f"billing/{template_base}_subject.txt", context).strip()
    body_txt = render_to_string(f"billing/{template_base}.txt", context)
    body_html = render_to_string(f"billing/{template_base}.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send(fail_silently=False)
        log.info("billing.email_sent", template=template_base, to=to)
        return True
    except Exception as exc:
        log.warning("billing.email_failed", template=template_base, to=to, error=str(exc))
        return False


def send_premium_activated(user) -> bool:
    return _send(template_base="premium_activated", to=user.email, context={})
