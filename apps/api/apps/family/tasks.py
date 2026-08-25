"""Celery tasks for the `family` app — Story 6.1 §T6.

Discovery: registered via `app.autodiscover_tasks()` in `path_advisor/celery.py`,
same mechanism as `apps.accounts.tasks`.
"""

from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from apps.family.models import ParentInvitation, ParentInvitationStatus, ParentStudentLink
from apps.family.services.emails import (
    send_invitation_accepted_to_student,
    send_invitation_to_parent,
    send_parent_link_revoked_to_parent,
)


@shared_task(name="family.expire_parent_invitations")
def expire_parent_invitations() -> int:
    """AC6 — daily sweep, 04:35 UTC. No notification sent (non-event, cf. AC6)."""
    updated = ParentInvitation.objects.filter(
        status=ParentInvitationStatus.PENDING,
        expires_at__lt=timezone.now(),
    ).update(status=ParentInvitationStatus.EXPIRED)
    return updated


@shared_task(name="family.send_parent_invitation_email")
def send_parent_invitation_email(invitation_id: str) -> bool:
    invitation = ParentInvitation.objects.select_related("student").filter(id=invitation_id).first()
    if invitation is None:
        return False
    return send_invitation_to_parent(invitation)


@shared_task(name="family.send_parent_invitation_accepted_email")
def send_parent_invitation_accepted_email(invitation_id: str, parent_id: str) -> bool:
    from apps.accounts.models import User

    invitation = ParentInvitation.objects.select_related("student").filter(id=invitation_id).first()
    parent = User.objects.filter(id=parent_id).first()
    if invitation is None or parent is None:
        return False
    return send_invitation_accepted_to_student(invitation, parent)


@shared_task(name="family.send_parent_link_revoked_email")
def send_parent_link_revoked_email(link_id: str) -> bool:
    link = ParentStudentLink.objects.select_related("parent", "student").filter(id=link_id).first()
    if link is None:
        return False
    return send_parent_link_revoked_to_parent(link)
