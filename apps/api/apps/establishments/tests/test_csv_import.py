"""Story 6.5 §T8.2 — CSV import: happy paths, skip reasons, encoding, row cap (AC3)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import ParentalConsent, UserRole, UserStatus
from apps.accounts.tests.factories import UserFactory
from apps.core import request_context
from apps.core.rls import bypass_rls, with_system_actor
from apps.establishments.models import (
    Cohort,
    CohortImportJob,
    CohortImportJobStatus,
    StudentImportInvitation,
)
from apps.establishments.services.cohort import create_cohort
from apps.establishments.services.student_import import import_row, parse_csv_rows
from apps.establishments.tests.factories import EstablishmentFactory

pytestmark = pytest.mark.django_db


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_establishments_user"):
        return UserFactory(**kwargs)


def _admin_client():
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True, is_staff=True)
    client = APIClient()
    # Code-review fix (2026-09): `force_authenticate` only overrides the
    # DRF-wrapped `Request.user` (set inside APIView.dispatch, after Django's
    # own middleware chain has already run). `TenantSessionMiddleware` reads
    # the raw Django `HttpRequest.user` (session-based, from
    # AuthenticationMiddleware) to set the Postgres RLS GUCs — with
    # `force_authenticate` it always sees AnonymousUser, so every write this
    # client makes is silently denied by RLS on a real Postgres role. This is
    # the first admin-WRITE endpoint in the repo to actually hit this (every
    # prior IsPathAdmin view was read-only). `force_login` sets a real
    # session, so AuthenticationMiddleware resolves `request.user` correctly
    # for every downstream middleware, exactly like a real browser session.
    #  itself triggers the `user_logged_in` signal
    # (`update_last_login`, a write to `users`) OUTSIDE any HTTP
    # request/middleware cycle — no GUC is set yet at that point, so the
    # write needs its own narrow bypass. Every subsequent `client.post/get`
    # goes through the real middleware chain with the now-real session,
    # which sets the GUCs correctly for the actual test assertions.
    with bypass_rls(reason="test_setup.force_login_update_last_login"):
        client.force_login(admin)
    client._admin = admin
    return client


def _make_cohort(admin_user) -> Cohort:
    # Code-review fix (2026-09): two INDEPENDENT mechanisms both need
    # satisfying here, on every backend — see the identical note in
    # test_student_import_invitation.py's `_make_cohort`:
    # 1. `TenantScopedModel.save()` (apps/core/models.py) is a Python-level
    #    guard that fails loud unless `request_context.get_actor_id()`
    #    returns something — runs on SQLite too, unrelated to RLS.
    # 2. `cohorts` is RLS-protected on Postgres — the actual INSERT needs
    #    `app.bypass_rls`/`app.actor_role` set as a Postgres session GUC,
    #    which only `with_system_actor`/`bypass_rls` do.
    with bypass_rls(reason="test_setup.create_establishment"):
        establishment = EstablishmentFactory()
    request_context.set_actor(admin_user)
    try:
        with with_system_actor(reason="test_setup.create_cohort"):
            return create_cohort(
                establishment=establishment, name="Terminale", school_year="2025-2026"
            )
    finally:
        request_context.clear()


def _import_row(*, cohort, row):
    # Code-review fix (2026-09): same reasoning — `import_row` writes `users`
    # + `student_import_invitations` (+ `parental_consents` for minors), all
    # RLS-protected in production this only ever runs inside a
    # `with_system_actor`-wrapped Celery task.
    with with_system_actor(reason="test_setup.import_row"):
        return import_row(cohort=cohort, row=row)


def _import_csv_url(cohort_id) -> str:
    return reverse("establishments:cohort-import-csv", kwargs={"cohort_id": cohort_id})


# ---------------------------------------------------------------------------
# Unit-level: parse_csv_rows + import_row (fast, no Celery/HTTP round-trip)
# ---------------------------------------------------------------------------


def test_parse_csv_rows_utf8():
    raw = b"nom,prenom,date_naissance,email,email_parent\nDupont,Alice,2008-01-01,alice@ex.test,\n"
    rows = parse_csv_rows(raw)
    assert rows == [
        {
            "nom": "Dupont",
            "prenom": "Alice",
            "date_naissance": "2008-01-01",
            "email": "alice@ex.test",
            "email_parent": "",
        }
    ]


def test_parse_csv_rows_latin1_fallback():
    raw = "nom,prenom,date_naissance,email,email_parent\nDupré,Éléa,2008-01-01,elea@ex.test,\n".encode(
        "latin-1"
    )
    rows = parse_csv_rows(raw)
    assert rows[0]["nom"] == "Dupré"


def test_import_row_majeur_creates_active_pending_invitation(settings):
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    cohort = _make_cohort(admin)

    result = _import_row(
        cohort=cohort,
        row={
            "nom": "Martin",
            "prenom": "Lea",
            "date_naissance": "2008-01-01",
            "email": "lea.martin@ex.test",
            "email_parent": "",
        },
    )

    assert result.skipped is False
    assert result.user.status == UserStatus.EMAIL_UNVERIFIED
    assert result.user.tenant_id == cohort.tenant_id
    assert result.user.has_usable_password() is False
    with bypass_rls(reason="test_assert.read_invitation"):
        assert StudentImportInvitation.objects.filter(user=result.user).exists()


def test_import_row_mineur_with_parent_email_triggers_parental_consent():
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    cohort = _make_cohort(admin)
    minor_birthdate = "2015-01-01"  # well under 15

    result = _import_row(
        cohort=cohort,
        row={
            "nom": "Petit",
            "prenom": "Sacha",
            "date_naissance": minor_birthdate,
            "email": "sacha.petit@ex.test",
            "email_parent": "parent@ex.test",
        },
    )

    assert result.skipped is False
    assert result.user.status == UserStatus.PENDING_PARENTAL_CONSENT
    with bypass_rls(reason="test_assert.read_invitation"):
        assert ParentalConsent.objects.filter(
            student=result.user, parent_email="parent@ex.test"
        ).exists()
        # Both minor and major students get their own invitation email (AC3).
        assert StudentImportInvitation.objects.filter(user=result.user).exists()


def test_import_row_mineur_without_parent_email_is_skipped():
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    cohort = _make_cohort(admin)

    result = _import_row(
        cohort=cohort,
        row={
            "nom": "Petit",
            "prenom": "Sacha",
            "date_naissance": "2015-01-01",
            "email": "sacha2@ex.test",
            "email_parent": "",
        },
    )

    assert result.skipped is True
    assert result.reason == "email_parent_requis_moins_15_ans"


def test_import_row_duplicate_email_is_skipped():
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    cohort = _make_cohort(admin)
    _uf(email="existing@ex.test")

    result = _import_row(
        cohort=cohort,
        row={
            "nom": "X",
            "prenom": "Y",
            "date_naissance": "2008-01-01",
            "email": "existing@ex.test",
            "email_parent": "",
        },
    )

    assert result.skipped is True
    assert result.reason == "email_deja_utilise"


def test_import_row_missing_email_is_skipped():
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    cohort = _make_cohort(admin)

    result = _import_row(
        cohort=cohort,
        row={
            "nom": "X",
            "prenom": "Y",
            "date_naissance": "2008-01-01",
            "email": "",
            "email_parent": "",
        },
    )

    assert result.skipped is True
    assert result.reason == "email_manquant"


# ---------------------------------------------------------------------------
# End-to-end: upload endpoint + Celery-eager job processing + poll endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_upload_csv_creates_job_and_processes_rows_synchronously_in_tests():
    """`CELERY_TASK_ALWAYS_EAGER=True` in test settings makes `.delay()` run
    in-process — EXCEPT that nothing in the test process ever imports
    `path_advisor.celery` (only the real worker process does, via `celery -A
    path_advisor worker`), so `@shared_task` binds to a bare default Celery
    app with non-Django config. `Task.apply()` sidesteps this entirely by
    always running locally regardless of broker config — same technique
    other Celery-task-dispatching endpoints in this repo work around by
    mocking `.delay` in their tests.
    """
    from apps.establishments.tasks import process_cohort_import

    client = _admin_client()
    cohort = _make_cohort(client._admin)

    csv_content = (
        "nom,prenom,date_naissance,email,email_parent\n"
        "Durand,Tom,2008-01-01,tom.durand@ex.test,\n"
        "Petit,Sacha,2015-01-01,sacha.p@ex.test,parent2@ex.test\n"
        "Existing,User,2008-01-01,existing2@ex.test,\n"
    )
    _uf(email="existing2@ex.test")

    upload = SimpleUploadedFile(
        "students.csv", csv_content.encode("utf-8"), content_type="text/csv"
    )
    with (
        patch(
            "apps.establishments.tasks.process_cohort_import.delay",
            side_effect=lambda job_id, rows: process_cohort_import.apply(args=(job_id, rows)),
        ),
        patch("apps.establishments.tasks.send_student_import_invitation_email.delay"),
    ):
        response = client.post(_import_csv_url(cohort.id), {"file": upload}, format="multipart")

    assert response.status_code == 202, response.content
    job_id = response.json()["job_id"]

    with bypass_rls(reason="test_assert.read_job"):
        job = CohortImportJob.objects.get(id=job_id)
    assert job.status == CohortImportJobStatus.COMPLETED
    assert job.total_rows == 3
    assert job.imported_count == 2
    assert job.skipped_count == 1
    assert {"row": 3, "reason": "email_deja_utilise"} in job.errors

    poll_url = reverse(
        "establishments:cohort-import-job-detail",
        kwargs={"cohort_id": cohort.id, "job_id": job_id},
    )
    poll_response = client.get(poll_url)
    assert poll_response.status_code == 200
    assert poll_response.json()["imported_count"] == 2


def test_upload_csv_over_2000_rows_returns_400():
    client = _admin_client()
    cohort = _make_cohort(client._admin)

    header = "nom,prenom,date_naissance,email,email_parent\n"
    rows = "".join(f"N,P,2008-01-01,student{i}@ex.test,\n" for i in range(2001))
    upload = SimpleUploadedFile(
        "students.csv", (header + rows).encode("utf-8"), content_type="text/csv"
    )

    response = client.post(_import_csv_url(cohort.id), {"file": upload}, format="multipart")

    assert response.status_code == 400, response.content
    assert not CohortImportJob.objects.filter(cohort=cohort).exists()
