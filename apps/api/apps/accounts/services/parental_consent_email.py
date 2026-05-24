"""Email dispatch helpers for the parental-consent flow (Story 1.4 T3).

Lives next to `parental_consent.py` so the dispatch site can call both the
domain service and the email helper from the same module path. Templates are
loaded from `apps/accounts/templates/parental_consent/` — `_subject.txt`, `.txt`,
`.html` triplets keyed by event name.

All emails are sent best-effort: a single SMTP failure surfaces as a structlog
warning but does not break the signup transaction (which has already committed
by the time the post-signup signal fires).
"""

from __future__ import annotations

import os

import structlog
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.accounts.models import ParentalConsent, User

log = structlog.get_logger(__name__)


def _site_url() -> str:
    """Same lookup logic as `PathAdvisorAccountAdapter.get_email_confirmation_url`.

    Centralised so changing the env var name only requires editing one place.
    """
    site_url = os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")
    return site_url.rstrip("/")


def _send(
    *,
    template_base: str,
    to: str,
    context: dict[str, object],
) -> bool:
    """Render + dispatch one email; return True iff SMTP accepted.

    Returns False on SMTP failure (logged + Sentry) so callers can branch — e.g.
    don't flip `reminder_sent_at` if the email never went out (Story 1.4 review §P6).
    """
    subject = render_to_string(f"parental_consent/{template_base}_subject.txt", context).strip()
    body_txt = render_to_string(f"parental_consent/{template_base}.txt", context)
    body_html = render_to_string(f"parental_consent/{template_base}.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send(fail_silently=False)
        log.info("parental_consent.email_sent", template=template_base, to=to)
        return True
    except Exception as exc:
        # Mirror the audit-log swallow contract: emails are observability events,
        # not transactional state. Sentry would catch this in prod.
        log.warning(
            "parental_consent.email_failed",
            template=template_base,
            to=to,
            error=str(exc),
        )
        return False


def send_request_to_parent(consent: ParentalConsent) -> bool:
    consent_url = f"{_site_url()}/auth/parental-consent/{consent.token}"
    return _send(
        template_base="parental_consent_request",
        to=consent.parent_email,
        context={"consent_url": consent_url, "consent": consent},
    )


def send_reminder_to_parent(consent: ParentalConsent) -> bool:
    consent_url = f"{_site_url()}/auth/parental-consent/{consent.token}"
    return _send(
        template_base="parental_consent_reminder",
        to=consent.parent_email,
        context={"consent_url": consent_url, "consent": consent},
    )


def send_granted_to_child(student: User) -> bool:
    login_url = f"{_site_url()}/auth/login"
    return _send(
        template_base="parental_consent_granted_to_child",
        to=student.email,
        context={"login_url": login_url, "student": student},
    )


def send_expired_to_child(student: User) -> bool:
    return _send(
        template_base="parental_consent_expired_to_child",
        to=student.email,
        context={"student": student},
    )
