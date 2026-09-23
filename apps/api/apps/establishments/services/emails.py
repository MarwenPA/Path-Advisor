"""Email dispatch for the establishments app — Story 6.5 §T6.

Story 8.1: sends go through `apps.mailer.send_transactional` — each call
persists a durable `EmailOutbox` row and delivery happens asynchronously
with exponential retry. The old "best-effort" contract (SMTP failure →
warning log → email silently lost) is gone: a failed delivery ends as a
non-silent `failed` outbox row, replayable via `retry_failed_emails`.
"""

from __future__ import annotations

import os

from apps.mailer.service import send_transactional


def _site_url() -> str:
    site_url = os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")
    return site_url.rstrip("/")


def _queue(*, template_base: str, to: str, context: dict[str, object]) -> bool:
    """Queue one transactional email; returns True (the row is durable).

    Kept as a `bool` so the Celery wrapper tasks in
    `apps.establishments.tasks` keep their return contract — "True" now
    means "durably queued", not "SMTP accepted".
    """
    send_transactional(
        template_app="establishments",
        template_base=template_base,
        to=to,
        context=context,
    )
    return True


def send_counselor_invitation(invitation) -> bool:
    invitation_url = f"{_site_url()}/auth/invitation-conseillere/{invitation.token}"
    return _queue(
        template_base="counselor_invitation",
        to=invitation.email,
        context={
            "establishment_name": invitation.establishment.name,
            "invitation_url": invitation_url,
        },
    )


def send_counselor_consent_requested(*, student, counselor) -> bool:
    """Story 6.7 AC — "Mme Dupont, ta conseillère, souhaite consulter ton profil"."""
    return _queue(
        template_base="counselor_consent_requested",
        to=student.email,
        context={"counselor_email": counselor.email},
    )


def send_student_import_invitation(invitation) -> bool:
    invitation_url = f"{_site_url()}/auth/invitation-eleve/{invitation.token}"
    return _queue(
        template_base="student_import_invitation",
        to=invitation.user.email,
        context={
            "establishment_name": invitation.cohort.establishment.name,
            "invitation_url": invitation_url,
        },
    )
