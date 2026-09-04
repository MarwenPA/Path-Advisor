"""Story 6.5 §T8.4 — student-import invitation accept: ≥15 → active, <15 →
stays pending_parental_consent (AC5)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.accounts.tests.factories import UserFactory
from apps.core import request_context
from apps.core.rls import bypass_rls, with_system_actor
from apps.establishments.models import StudentImportInvitationStatus
from apps.establishments.services.cohort import create_cohort
from apps.establishments.services.student_import import import_row
from apps.establishments.tests.factories import EstablishmentFactory

pytestmark = pytest.mark.django_db


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_establishments_user"):
        return UserFactory(**kwargs)


def _accept_url(token: str) -> str:
    return reverse("establishments_students:student-invitation-accept", kwargs={"token": token})


def _status_url(token: str) -> str:
    return reverse("establishments_students:student-invitation-status", kwargs={"token": token})


def _make_cohort():
    # Code-review fix (2026-09): two INDEPENDENT mechanisms both need
    # satisfying here, on every backend:
    # 1. `TenantScopedModel.save()` (apps/core/models.py) is a Python-level
    #    guard that fails loud unless `request_context.get_actor_id()`
    #    returns something — this runs on SQLite too, it has nothing to do
    #    with RLS. `request_context.set_actor(admin)` satisfies it.
    # 2. `cohorts` is RLS-protected on Postgres — the actual INSERT is denied
    #    without `app.bypass_rls`/`app.actor_role='path_admin'` set as a
    #    Postgres session GUC, which `request_context.set_actor` does NOT do
    #    (that's a Python thread-local, not a DB-level setting). Only
    #    `with_system_actor`/`bypass_rls` set the GUC.
    # The original code only had (1) — it silently worked on SQLite (no RLS)
    # and was never run against real Postgres until this review.
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    with bypass_rls(reason="test_setup.create_establishment"):
        establishment = EstablishmentFactory()
    request_context.set_actor(admin)
    try:
        with with_system_actor(reason="test_setup.create_cohort"):
            return create_cohort(
                establishment=establishment, name="Terminale", school_year="2025-2026"
            )
    finally:
        request_context.clear()


def _import_row(*, cohort, row):
    # Code-review fix (2026-09): `import_row` writes `users` +
    # `student_import_invitations` (both RLS-protected) — in production it
    # only ever runs inside the Celery task, which wraps itself in
    # `with_system_actor`. A bare call here (no request, no actor) is denied
    # by RLS on a real Postgres role.
    with with_system_actor(reason="test_setup.import_row"):
        return import_row(cohort=cohort, row=row)


def test_accept_majeur_activates_account():
    cohort = _make_cohort()
    result = _import_row(
        cohort=cohort,
        row={
            "nom": "M",
            "prenom": "A",
            "date_naissance": "2008-01-01",
            "email": "majeur@ex.test",
            "email_parent": "",
        },
    )
    invitation = result.invitation
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json"
    )

    assert response.status_code == 200, response.content
    with bypass_rls(reason="test_assert.read_student"):
        student = User.objects.get(id=result.user.id)
    assert student.status == UserStatus.ACTIVE
    assert student.email_verified_at is not None
    assert student.check_password("Path-Advisor-2026!")
    with bypass_rls(reason="test_assert.read_invitation"):
        invitation.refresh_from_db()
    assert invitation.status == StudentImportInvitationStatus.ACCEPTED


def test_accept_mineur_keeps_pending_parental_consent():
    cohort = _make_cohort()
    result = _import_row(
        cohort=cohort,
        row={
            "nom": "M",
            "prenom": "A",
            "date_naissance": "2015-01-01",
            "email": "mineur@ex.test",
            "email_parent": "parent@ex.test",
        },
    )
    invitation = result.invitation
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json"
    )

    assert response.status_code == 200, response.content
    with bypass_rls(reason="test_assert.read_student"):
        student = User.objects.get(id=result.user.id)
    # Password IS set even though status stays pending (AC5 last clause).
    assert student.status == UserStatus.PENDING_PARENTAL_CONSENT
    assert student.check_password("Path-Advisor-2026!")


def test_accept_without_password_returns_400():
    cohort = _make_cohort()
    result = _import_row(
        cohort=cohort,
        row={
            "nom": "M",
            "prenom": "A",
            "date_naissance": "2008-01-01",
            "email": "nopass@ex.test",
            "email_parent": "",
        },
    )
    client = APIClient()

    response = client.post(_accept_url(result.invitation.token), {}, format="json")

    assert response.status_code == 400


def test_accept_expired_token_returns_404():
    cohort = _make_cohort()
    result = _import_row(
        cohort=cohort,
        row={
            "nom": "M",
            "prenom": "A",
            "date_naissance": "2008-01-01",
            "email": "expired@ex.test",
            "email_parent": "",
        },
    )
    invitation = result.invitation
    invitation.expires_at = timezone.now() - timezone.timedelta(days=1)
    with with_system_actor(reason="test_setup.expire_invitation"):
        invitation.save(update_fields=["expires_at"])
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json"
    )

    assert response.status_code == 404


def test_status_endpoint_unknown_token_returns_404():
    client = APIClient()
    response = client.get(_status_url("does-not-exist"))
    assert response.status_code == 404
