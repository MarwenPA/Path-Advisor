"""Story 10.2 — the Web Push delivery channel.

Push is a SECONDARY channel layered on the Story 8.2 engine: `notify()`
enqueues `send_web_push` next to the email when the caller provides a
`push` payload. Email stays the durable channel — a failed push is logged,
never retried (a retry after the email landed would duplicate the
information with worse copy; the AC's guarantee is "informé", and the email
is that guarantee).

Privacy: the payload may surface on a LOCKED screen, so callers keep it
generic (no school name, no personal data — "Une école t'a répondu", never
which one). The payload is aes128gcm-encrypted end-to-end (RFC 8291): the
push service (FCM/Mozilla/APNs) relays bytes it cannot read.

Configuration: empty `WEBPUSH_VAPID_PRIVATE_KEY` disables the channel
entirely (email-only degradation, NFR-R4) — dev generates a local pair with
`manage.py generate_vapid_keys` (the private key is a secret: .env only).
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from django.conf import settings
from pywebpush import WebPushException, webpush

from .models import PushSubscription, is_enabled

log = structlog.get_logger(__name__)

#: Push services drop undeliverable messages after this TTL — one day: a
#: calendar reminder or school response older than that is stale news the
#: next email/app visit covers better than a late buzz.
PUSH_TTL_SECONDS = 86_400


def deliver_web_push(*, user_id: str, category: str, payload: dict[str, Any]) -> dict[str, int]:
    """Send `payload` to every subscription of `user_id`. Returns counters.

    Mirrors `deliver_email`'s delivery-time re-checks: the opt-out gate runs
    again here (the user may have unsubscribed between enqueue and send).
    A 404/410 from the push service means the browser revoked the
    subscription → the row is purged (AC2: no push after deactivation).
    """
    if not settings.WEBPUSH_VAPID_PRIVATE_KEY:
        log.info("notifications.push_unconfigured", user_id=user_id, category=category)
        return {"sent": 0, "purged": 0, "failed": 0}

    if not is_enabled(user_id, category):
        log.info("notifications.push_skipped_opted_out", user_id=user_id, category=category)
        return {"sent": 0, "purged": 0, "failed": 0}

    data = json.dumps(payload, ensure_ascii=False)
    sent = purged = failed = 0
    for subscription in PushSubscription.objects.filter(user_id=user_id):
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=data,
                ttl=PUSH_TTL_SECONDS,
                vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.WEBPUSH_VAPID_ADMIN_EMAIL}"},
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                # The browser revoked this subscription — purge, silently.
                subscription.delete()
                purged += 1
            else:
                failed += 1
                log.error(
                    "notifications.push_delivery_failed",
                    user_id=user_id,
                    category=category,
                    status=status,
                )
    log.info(
        "notifications.push_dispatched",
        user_id=user_id,
        category=category,
        sent=sent,
        purged=purged,
        failed=failed,
    )
    return {"sent": sent, "purged": purged, "failed": failed}
