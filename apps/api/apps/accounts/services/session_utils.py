"""Session-purge helper — shared between Story 1.12 (account deletion) and Story 1.5 (password reset).

Both stories need to invalidate a user's active Django sessions when their
credentials state changes:

- Account soft-delete: session must die immediately so the deleted user can't
  keep a tab alive past `is_active=False` (Story 1.12 §AC1 step 3).
- Password reset confirm: every existing session uses the OLD password's
  derived state and must be invalidated so a stolen session cookie can't
  outlive the password rotation (Story 1.5 §AC6).

Sessions are NOT FK-linked to the User model (Django stores `_auth_user_id`
inside the encoded payload). The DB backend (default for MVP) requires a
walk + decode of every active row; a Sprint-4+ Redis session backend would
reduce this to a single SCAN+DEL — see deferred-work.

The bare-except on `sess.get_decoded()` is intentional (Story 1.12 §P15):
a SECRET_KEY rotation, a corrupted payload from a manual DB poke, or a
Django version that changed the signing format must not block the whole
purge on one bad row. The decode failure is structured-logged so an
operational flurry surfaces in observability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from django.contrib.sessions.models import Session
from django.utils import timezone

if TYPE_CHECKING:
    from apps.accounts.models import User

log = structlog.get_logger(__name__)


def terminate_user_sessions(user: User) -> int:
    """Delete every active Django session whose payload matches this user.

    Returns the count of sessions killed so the caller's audit metadata can
    record the blast radius.

    Two-phase: collect matching session keys first, then bulk-delete by
    `session_key__in=...`. The previous design called `sess.delete()` while
    walking the iterator, which mutates the result set mid-cursor and can
    skip boundary rows on some DB drivers (code-review P8 — Story 1.5 review
    2026-05-27).
    """
    user_id_str = str(user.pk)
    keys_to_kill: list[str] = []
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for sess in active_sessions.iterator(chunk_size=200):
        try:
            data = sess.get_decoded()
        except Exception as exc:
            log.warning(
                "accounts.session_decode_failed",
                session_key_prefix=(sess.session_key or "")[:6],
                error_type=exc.__class__.__name__,
            )
            continue
        if data.get("_auth_user_id") == user_id_str:
            keys_to_kill.append(sess.session_key)

    if not keys_to_kill:
        return 0
    deleted, _ = Session.objects.filter(session_key__in=keys_to_kill).delete()
    return deleted
