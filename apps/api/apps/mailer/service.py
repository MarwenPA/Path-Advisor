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
    notification_user_id: str = "",
    notification_category: str = "",
) -> EmailOutbox:
    """Queue a transactional email; returns its durable outbox row.

    `context` must be JSON-serializable (the row has to survive a process
    restart) — enforced here so a model instance slipped into a context
    fails at the call site, not later inside a worker where the traceback
    points at nothing useful.

    `notification_user_id`/`notification_category` are set ONLY by the
    notifications engine: they let `deliver_email` re-check the opt-out at
    delivery time and build the legal footer (unsubscribe token included)
    at render time instead of persisting capability URLs in `context`
    (review fixes P2-6 / P2-11).
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
        notification_user_id=notification_user_id,
        notification_category=notification_category,
    )
    # robust=True (review fix P1-1): during batch sends, one hook that fails
    # on a broker blip must not abandon the remaining hooks — Django logs
    # the exception and keeps going; the stale-QUEUED sweeper is the safety
    # net for the row whose hook failed.
    transaction.on_commit(lambda: deliver_email.delay(row.pk), robust=True)
    return row
