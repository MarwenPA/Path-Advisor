"""Story 8.1 — the one entry point every sender goes through.

`send_transactional` replaces the eight copies of the best-effort
render-and-send helper. It persists an `EmailOutbox` row and enqueues
delivery via `transaction.on_commit`, so:

- a rolled-back business transaction never emails anyone about something
  that did not happen;
- the Celery worker can never race a row that is not committed yet;
- an SMTP outage costs retries, not the email (AC3 / NFR-R4).

The name keeps the AC's vocabulary (`sendTransactional`) — the "provider
interface" itself stays Django's `EMAIL_BACKEND`, which already switches
Mailpit/Postmark/console per environment without code changes (see the
story doc §2 for why we refused to reinvent that wheel).
"""

from __future__ import annotations

import json

from django.db import transaction

from .models import EmailOutbox
from .tasks import deliver_email


def send_transactional(
    *,
    template_app: str,
    template_base: str,
    to: str,
    context: dict[str, object],
) -> EmailOutbox:
    """Queue a transactional email; returns its durable outbox row.

    `context` must be JSON-serializable (the row has to survive a process
    restart) — enforced here so a model instance slipped into a context
    fails at the call site, not later inside a worker where the traceback
    points at nothing useful.
    """
    try:
        json.dumps(context)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            "send_transactional(context=...) must be JSON-serializable — got "
            f"an invalid value: {exc}. Pass ids/strings, not model instances."
        ) from exc

    row = EmailOutbox.objects.create(
        to=to,
        template_app=template_app,
        template_base=template_base,
        context=context,
    )
    transaction.on_commit(lambda: deliver_email.delay(row.pk))
    return row
