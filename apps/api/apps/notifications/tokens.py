"""Story 8.2 — signed unsubscribe tokens (the legal footer link).

`django.core.signing` with a dedicated salt; **no expiry on purpose** — an
unsubscribe link at the bottom of a six-month-old email must still work
(the legal obligation has no TTL). The token carries only (user_id,
category); tampering breaks the signature, and an unknown category is
rejected at use time.
"""

from __future__ import annotations

from django.core import signing

from .models import NotificationCategory

_SALT = "notifications.unsubscribe.v1"


def make_unsubscribe_token(user_id: str, category: str) -> str:
    return signing.dumps({"u": user_id, "c": category}, salt=_SALT)


def read_unsubscribe_token(token: str) -> tuple[str, str] | None:
    """Returns (user_id, category), or None for any invalid/foreign token."""
    try:
        payload = signing.loads(token, salt=_SALT)
    except signing.BadSignature:
        return None
    user_id, category = payload.get("u"), payload.get("c")
    if not user_id or category not in NotificationCategory.values:
        return None
    return user_id, category
