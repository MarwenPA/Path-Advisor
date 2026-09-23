"""Account-deletion transactional emails — Story 1.12.

Three templates, sent on different lifecycle transitions:

    - `account_deletion_requested.{txt,html}` — soft-delete confirmation +
      cancel-link. Queued inside the request_deletion transaction (Story 1.12
      §AC4 atomicity invariant, restated under Story 8.1: the durable
      `EmailOutbox` row commits — or rolls back — WITH the wipe, so the user
      is notified iff the soft-delete persisted; an SMTP outage now costs
      retries, never the email and never the deletion).
    - `account_deletion_cancelled.{txt,html}` — restoration acknowledgment.
    - `account_deletion_completed.{txt,html}` — last message to this address,
      queued at the hard-delete moment; delivery is retried by the outbox and
      can never block the wipe (it runs after commit).

All three follow the "voix complice, non-culpabilisante" tone of Stories 1.3 /
1.4 — no legalese, no urgency-pressure, French only. Hosting URL comes from
`NEXT_PUBLIC_SITE_URL` (same env var the allauth adapter uses for verify-email
links).

Story 8.1: sends go through `apps.mailer.send_transactional` — subjects moved
from Python literals into `*_subject.txt` templates (the outbox rendering
convention). The Story 1.12 §P21 locale guarantee (French month names even on
an `LANG=C` worker) is preserved by pre-formatting the only locale-sensitive
value (`hard_delete_after`) under `translation.override("fr-FR")` at enqueue
time — outbox contexts must be JSON-serializable, so the datetime cannot ride
along raw.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import formats, timezone, translation

from apps.mailer.service import send_transactional

if TYPE_CHECKING:
    import datetime

    from apps.accounts.models import AccountDeletionRequest, User


def _build_cancel_url(token: str) -> str:
    """Return the public landing URL for the cancel flow.

    Front-end route: `/auth/cancel-deletion/<token>`. Mirrors the
    parental-consent landing convention from Story 1.4.

    Story 1.12 code review §P12: use `urljoin` + `quote` instead of raw
    string concatenation so a misconfigured `NEXT_PUBLIC_SITE_URL` with an
    embedded path (e.g. `https://app.example.com/api`) or a future token
    scheme with URL-reserved characters does not silently break the link.
    """
    site_url = os.environ.get("NEXT_PUBLIC_SITE_URL")
    if not site_url:
        if not settings.DEBUG:
            raise ImproperlyConfigured(
                "NEXT_PUBLIC_SITE_URL must be set in non-DEBUG environments "
                "to build account-deletion cancel links."
            )
        site_url = "http://localhost:3000"
    # `urljoin` resolves against the host portion only when the base ends
    # with '/' — explicit trailing slash + relative second arg gives the
    # expected `{host}/auth/cancel-deletion/{token}` shape.
    safe_token = quote(token, safe="")
    return urljoin(site_url.rstrip("/") + "/", f"auth/cancel-deletion/{safe_token}")


def _format_fr(dt: datetime.datetime) -> str:
    """Render a datetime the way `{{ dt|date:"j F Y à H:i" }}` used to.

    Story 1.12 code review §P21: force the `fr-FR` locale so month names come
    out French regardless of the enqueuing process's locale; `localtime`
    reproduces the template engine's automatic conversion to
    `settings.TIME_ZONE` (Europe/Paris).
    """
    with translation.override("fr-FR"):
        return formats.date_format(timezone.localtime(dt), "j F Y à H:i")


def _queue(*, template_base: str, to: str, context: dict[str, object]) -> None:
    """Queue one transactional email as a durable `EmailOutbox` row.

    Rendering (subject + bodies) happens in the mailer worker under the
    project default locale (`LANGUAGE_CODE = "fr-fr"`); anything
    locale-formatted is pre-formatted here (cf. `_format_fr`).
    """
    send_transactional(
        template_app="accounts",
        template_base=template_base,
        to=to,
        context=context,
    )


def send_account_deletion_requested_email(
    *,
    user: User,
    deletion: AccountDeletionRequest,
) -> None:
    """Soft-delete confirmation — contains the cancel link, valid 30 days."""
    _queue(
        template_base="email/account_deletion_requested",
        to=user.email,
        context={
            "cancel_url": _build_cancel_url(deletion.cancel_token),
            "hard_delete_after": _format_fr(deletion.hard_delete_after),
        },
    )


def send_account_deletion_cancelled_email(
    *,
    user: User,
    deletion: AccountDeletionRequest,
) -> None:
    """Restoration acknowledgment after a successful cancel."""
    _queue(
        template_base="email/account_deletion_cancelled",
        to=user.email,
        context={},
    )


def send_account_deletion_completed_email(
    *,
    user: User,
    deletion: AccountDeletionRequest,
) -> None:
    """Final notification at hard-delete time.

    Queued inside the hard-delete transaction; delivered after commit. The
    legal obligation is the data wipe, not the notification (story §4.5 #9) —
    with the outbox that ordering is structural: enqueue cannot fail for SMTP
    reasons, and delivery (with retries) happens strictly after the wipe
    committed. The row itself is bounded by `prune_email_outbox` retention.
    """
    _queue(
        template_base="email/account_deletion_completed",
        to=user.email,
        context={},
    )
