"""Email dispatch helpers for the parent-invitation flow (Story 6.1 §T4).

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

    Kept as a `bool` so the existing Celery wrapper tasks in
    `apps.family.tasks` keep their return contract — "True" now means
    "durably queued", not "SMTP accepted".
    """
    send_transactional(
        template_app="family",
        template_base=template_base,
        to=to,
        context=context,
    )
    return True


def send_invitation_to_parent(invitation) -> bool:
    invitation_url = f"{_site_url()}/auth/invitation-parent/{invitation.token}"
    return _queue(
        template_base="parent_invitation",
        to=invitation.parent_email,
        context={
            "student_first_name": invitation.student.email.split("@")[0],
            "custom_message": invitation.custom_message,
            "invitation_url": invitation_url,
        },
    )


def send_invitation_accepted_to_student(invitation, parent) -> bool:
    return _queue(
        template_base="parent_invitation_accepted_to_student",
        to=invitation.student.email,
        context={
            "student_first_name": invitation.student.email.split("@")[0],
            "parent_first_name": parent.email.split("@")[0],
        },
    )


def send_parent_link_revoked_to_parent(link) -> bool:
    return _queue(
        template_base="parent_link_revoked_to_parent",
        to=link.parent.email,
        context={"student_first_name": link.student.email.split("@")[0]},
    )
