"""Email dispatch for billing — Story 5.3 §T5.

Story 8.1: sends go through `apps.mailer.send_transactional` — the call
persists a durable `EmailOutbox` row inside the webhook transaction (the
activation and its confirmation email commit — or roll back — together) and
delivery happens asynchronously after commit with exponential retry. The old
"best-effort" contract (SMTP failure → warning log → email silently lost) is
gone: a failed delivery ends as a non-silent `failed` outbox row, replayable
via `retry_failed_emails`.
"""

from __future__ import annotations

from apps.mailer.service import send_transactional


def send_premium_activated(user) -> bool:
    """Queue the premium-activation confirmation; True means durably queued."""
    send_transactional(
        template_app="billing",
        template_base="premium_activated",
        to=user.email,
        context={},
    )
    return True
