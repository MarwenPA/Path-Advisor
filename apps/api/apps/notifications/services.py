"""Story 8.2 — the notification engine.

`notify()` is the ONLY sanctioned way to send a category email. It is a
thin, opinionated layer over Story 8.1's `send_transactional`:

1. **Preference gate at the point of send** (AC3): an unsubscribed user is
   a logged no-op — the guarantee lives here, not in the UI, so a future
   sender (8.3-8.5) cannot forget it.
2. **Legal footer injection** (AC2): every category email gets
   `manage_notifications_url` and a per-(user, category) signed
   `unsubscribe_url` — built by `deliver_email` at RENDER time from the
   row's `notification_user_id`/`notification_category` (review fix P2-6:
   a signed no-expiry capability URL must never be persisted in the outbox
   `context`). The shared base template renders them; a category template
   that skips the base loses the footer.

Deliberately NOT handled here: rendering, retry, durability — that is the
outbox's job (8.1). One responsibility per layer.
"""

from __future__ import annotations

import structlog

from apps.mailer.models import EmailOutbox
from apps.mailer.service import send_transactional

from .models import NotificationCategory, is_enabled

log = structlog.get_logger(__name__)


def notify(
    *,
    user_id: str,
    email: str,
    category: str,
    template_app: str,
    template_base: str,
    context: dict[str, object],
) -> EmailOutbox | None:
    """Send a category notification — or refuse, loudly-in-logs, if opted out.

    Returns the outbox row, or None when the user is unsubscribed (callers
    must treat None as success: "not sent because the user said no" is a
    normal outcome, not an error).
    """
    if category not in NotificationCategory.values:
        raise ValueError(f"Unknown notification category: {category!r}")

    if not is_enabled(user_id, category):
        # AC3's enforcement point. INFO on purpose: this is the system
        # working as designed, but it must stay observable (FR47 disputes
        # are settled by this line + the preference row's updated_at).
        log.info("notifications.skipped_opted_out", user_id=user_id, category=category)
        return None

    return send_transactional(
        template_app=template_app,
        template_base=template_base,
        to=email,
        context=context,
        # The delivery task re-checks the opt-out (P2-11) and builds the
        # footer URLs at render time (P2-6) from these two fields.
        notification_user_id=user_id,
        notification_category=category,
    )
