"""Email dispatch helpers for the parental-consent flow (Story 1.4 T3).

Lives next to `parental_consent.py` so the dispatch site can call both the
domain service and the email helper from the same module path. Templates are
loaded from `apps/accounts/templates/parental_consent/` — `_subject.txt`, `.txt`,
`.html` triplets keyed by event name.

Story 8.1: every send goes through `apps.mailer.send_transactional`. Each
call persists a durable `EmailOutbox` row inside the caller's transaction;
delivery runs asynchronously with exponential retry and a loud, replayable
`failed` terminal state. The pre-8.1 "best-effort" contract (SMTP failure →
structlog warning → email silently lost) no longer exists: `True` now means
"durably queued", and callers that used to gate DB stamps on "SMTP accepted"
(e.g. `reminder_sent_at`) now stamp on durable enqueue — the delivery
guarantee lives in `apps.mailer`, not at the call site.
"""

from __future__ import annotations

import os

from apps.accounts.models import ParentalConsent, User
from apps.mailer.service import send_transactional


def _site_url() -> str:
    """Same lookup logic as `PathAdvisorAccountAdapter.get_email_confirmation_url`.

    Centralised so changing the env var name only requires editing one place.
    """
    site_url = os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")
    return site_url.rstrip("/")


def _queue(
    *,
    template_base: str,
    to: str,
    context: dict[str, object],
) -> bool:
    """Queue one transactional email; returns True (the row is durable).

    Context values must be JSON-serializable (`send_transactional` enforces
    it) — the templates only consume plain URLs, so no model instance ever
    enters the outbox row.
    """
    send_transactional(
        template_app="parental_consent",
        template_base=template_base,
        to=to,
        context=context,
    )
    return True


def send_request_to_parent(consent: ParentalConsent) -> bool:
    consent_url = f"{_site_url()}/auth/parental-consent/{consent.token}"
    return _queue(
        template_base="parental_consent_request",
        to=consent.parent_email,
        context={"consent_url": consent_url},
    )


def send_reminder_to_parent(consent: ParentalConsent) -> bool:
    consent_url = f"{_site_url()}/auth/parental-consent/{consent.token}"
    return _queue(
        template_base="parental_consent_reminder",
        to=consent.parent_email,
        context={"consent_url": consent_url},
    )


def send_granted_to_child(student: User) -> bool:
    login_url = f"{_site_url()}/auth/login"
    return _queue(
        template_base="parental_consent_granted_to_child",
        to=student.email,
        context={"login_url": login_url},
    )


def send_expired_to_child(student: User) -> bool:
    return _queue(
        template_base="parental_consent_expired_to_child",
        to=student.email,
        context={},
    )


def send_revoked_to_parent(consent: ParentalConsent) -> bool:
    """Story 1.10 §AC4 — notify the parent that the student revoked their access.

    Returns True once the email is durably queued (Story 8.1); the Celery task
    gates `notification_sent_at` on this return value (idempotency contract —
    second invocation is a no-op after the first successful enqueue). Delivery
    retries and terminal failure visibility are owned by `apps.mailer`.
    """
    return _queue(
        template_base="parental_consent_revoked_to_parent",
        to=consent.parent_email,
        context={},
    )
