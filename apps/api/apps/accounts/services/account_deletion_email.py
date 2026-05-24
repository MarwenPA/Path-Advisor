"""Account-deletion transactional emails — Story 1.12.

Three templates, sent on different lifecycle transitions:

    - `account_deletion_requested.{txt,html}` — soft-delete confirmation +
      cancel-link. Sent synchronously inside the request_deletion transaction
      (Story 1.12 §AC4 atomicity invariant: SMTP failure rolls back the wipe).
    - `account_deletion_cancelled.{txt,html}` — restoration acknowledgment.
    - `account_deletion_completed.{txt,html}` — last message to this address,
      sent at the hard-delete moment; SMTP failures here are best-effort.

All three follow the "voix complice, non-culpabilisante" tone of Stories 1.3 /
1.4 — no legalese, no urgency-pressure, French only. Hosting URL comes from
`NEXT_PUBLIC_SITE_URL` (same env var the allauth adapter uses for verify-email
links).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

if TYPE_CHECKING:
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


def _send(
    *,
    subject: str,
    template: str,
    to: str,
    context: dict,
) -> None:
    """Render + dispatch one transactional email. Raises on SMTP failure.

    Story 1.12 code review §P21: render templates under the `fr-FR` locale
    so `{{ ...|date:"j F Y" }}` outputs French month names ("23 juin 2026")
    even when the Celery worker runs with `LANG=C` / en-US as default.
    """
    with translation.override("fr-FR"):
        html_body = render_to_string(f"{template}.html", context)
        text_body = render_to_string(f"{template}.txt", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


def send_account_deletion_requested_email(
    *,
    user: User,
    deletion: AccountDeletionRequest,
) -> None:
    """Soft-delete confirmation — contains the cancel link, valid 30 days."""
    _send(
        subject="[Path-Advisor] Demande de suppression de compte reçue — tu as 30 jours pour annuler",
        template="accounts/email/account_deletion_requested",
        to=user.email,
        context={
            "user": user,
            "deletion": deletion,
            "cancel_url": _build_cancel_url(deletion.cancel_token),
            "hard_delete_after": deletion.hard_delete_after,
        },
    )


def send_account_deletion_cancelled_email(
    *,
    user: User,
    deletion: AccountDeletionRequest,
) -> None:
    """Restoration acknowledgment after a successful cancel."""
    _send(
        subject="[Path-Advisor] Suppression annulée — ton compte est restauré",
        template="accounts/email/account_deletion_cancelled",
        to=user.email,
        context={"user": user, "deletion": deletion},
    )


def send_account_deletion_completed_email(
    *,
    user: User,
    deletion: AccountDeletionRequest,
) -> None:
    """Final notification at hard-delete time.

    Caller MUST wrap this in try/except — story §4.5 #9: the legal obligation
    is the data wipe, not the notification. A bouncing inbox cannot block the
    deletion.
    """
    _send(
        subject="[Path-Advisor] Ton compte et tes données ont été supprimés",
        template="accounts/email/account_deletion_completed",
        to=user.email,
        context={"user": user, "deletion": deletion},
    )
