"""Celery tasks for the `establishments` app — Story 6.5 §T3/§T6.

Discovery: registered via `app.autodiscover_tasks()` in `path_advisor/celery.py`.
"""

from __future__ import annotations

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.core.rls import with_system_actor
from apps.establishments.models import (
    Cohort,
    CohortImportJob,
    CohortImportJobStatus,
    CounselorInvitation,
    StudentImportInvitation,
)
from apps.establishments.services.emails import (
    send_counselor_invitation,
    send_student_import_invitation,
)
from apps.establishments.services.student_import import ImportRowResult, import_row


@shared_task(name="establishments.process_cohort_import")
def process_cohort_import(job_id: str, rows: list[dict]) -> dict:
    """§T3.1 — process the already-parsed CSV rows for one `CohortImportJob`.

    Every row is processed in its own isolated `try/except` so a single bad
    row (unexpected exception, not just a typed skip reason) never aborts
    the rest of the CSV (§AC3 last clause / §4.5 risk table). The job is
    always finalized (`completed` or `failed`) — never left `processing`.
    """
    with with_system_actor(reason="establishments.process_cohort_import"):
        try:
            job = CohortImportJob.objects.select_related("cohort").get(id=job_id)
        except CohortImportJob.DoesNotExist:
            return {"status": "missing_job", "job_id": job_id}

        job.status = CohortImportJobStatus.PROCESSING
        job.total_rows = len(rows)
        job.save(update_fields=["status", "total_rows"])

        cohort: Cohort = job.cohort
        imported = 0
        skipped = 0
        errors: list[dict] = []
        invitation_ids: list[str] = []

        for index, row in enumerate(rows, start=1):
            try:
                result: ImportRowResult = import_row(cohort=cohort, row=row)
            except Exception as exc:
                skipped += 1
                errors.append(
                    {"row": index, "reason": f"erreur_inattendue:{exc.__class__.__name__}"}
                )
                continue

            if result.skipped:
                skipped += 1
                errors.append({"row": index, "reason": result.reason})
                continue

            imported += 1
            if result.invitation is not None:
                invitation_ids.append(result.invitation.id)

        job.imported_count = imported
        job.skipped_count = skipped
        job.errors = errors
        job.status = CohortImportJobStatus.COMPLETED
        job.completed_at = timezone.now()
        job.save(
            update_fields=[
                "imported_count",
                "skipped_count",
                "errors",
                "status",
                "completed_at",
            ]
        )

        transaction.on_commit(
            lambda: [send_student_import_invitation_email.delay(iid) for iid in invitation_ids]
        )

    return {"status": "completed", "imported": imported, "skipped": skipped}


@shared_task(name="establishments.send_counselor_invitation_email")
def send_counselor_invitation_email(invitation_id: str) -> bool:
    invitation = (
        CounselorInvitation.objects.select_related("establishment").filter(id=invitation_id).first()
    )
    if invitation is None:
        return False
    return send_counselor_invitation(invitation)


@shared_task(name="establishments.send_student_import_invitation_email")
def send_student_import_invitation_email(invitation_id: str) -> bool:
    invitation = (
        StudentImportInvitation.objects.select_related("user", "cohort__establishment")
        .filter(id=invitation_id)
        .first()
    )
    if invitation is None:
        return False
    return send_student_import_invitation(invitation)
