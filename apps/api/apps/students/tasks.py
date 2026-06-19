"""Celery tasks for the students app — Story 2.2 domain events."""

from __future__ import annotations

import logging

from celery import shared_task

log = logging.getLogger(__name__)


@shared_task(
    name="students.emit_student_level_declared",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
)
def emit_student_level_declared(level_profile_id: str) -> None:
    """Publish `student_level_declared` domain event (Story 2.2 AC9).

    Today this is a no-op stub — the downstream consumers (Epic 3 reco engine,
    Epic 8 notifications) are not yet built. The Celery task boundary is the
    extension point: when Epic 3 ships, it registers a consumer here or on the
    outbox table that this task would populate.

    The task is idempotent: if the same level_profile_id is emitted twice
    (re-edit after completion), downstream consumers must handle the update
    (AC9 "idempotent" requirement).
    """
    from apps.students.models import StudentLevelProfile

    try:
        level_profile = StudentLevelProfile.objects.select_related("profile__user").get(
            pk=level_profile_id
        )
    except StudentLevelProfile.DoesNotExist:
        log.warning("emit_student_level_declared: level_profile %s not found", level_profile_id)
        return

    log.info(
        "student_level_declared",
        extra={
            "student_id": str(level_profile.profile.user_id),
            "level": level_profile.level,
            "filiere": level_profile.filiere,
            "specialites": level_profile.specialites,
            "intended_track": level_profile.intended_track,
            "level_profile_id": level_profile_id,
        },
    )
    # Future: outbox.publish("student_level_declared", payload={...})
