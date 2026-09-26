"""Story 8.2 — the notification engine.

`notify()` is the ONLY sanctioned way to send a category email. It is a
thin, opinionated layer over Story 8.1's `send_transactional`:

1. **Preference gate at the point of send** (AC3): an unsubscribed user is
   a logged no-op — the guarantee lives here, not in the UI, so a future
   sender (8.3-8.5) cannot forget it.
2. **Legal footer injection** (AC2): every category email gets
   `manage_notifications_url` and a per-(user, category) signed
   `unsubscribe_url` in its context; the shared base template renders
   them. A category template that skips the base loses the footer — the
   demo template shows the intended `{% extends %}` shape.

Deliberately NOT handled here: rendering, retry, durability — that is the
outbox's job (8.1). One responsibility per layer.
"""

from __future__ import annotations

import os

import structlog

from apps.mailer.models import EmailOutbox
from apps.mailer.service import send_transactional

from .models import NotificationCategory, is_enabled
from .tokens import make_unsubscribe_token

log = structlog.get_logger(__name__)


def _site_url() -> str:
    return os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")


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

    footer = {
        "manage_notifications_url": f"{_site_url()}/parametres/notifications",
        "unsubscribe_url": (
            f"{_site_url()}/desinscription/{make_unsubscribe_token(user_id, category)}"
        ),
        "category_label": NotificationCategory(category).label,
    }
    return send_transactional(
        template_app=template_app,
        template_base=template_base,
        to=email,
        context={**context, **footer},
    )
