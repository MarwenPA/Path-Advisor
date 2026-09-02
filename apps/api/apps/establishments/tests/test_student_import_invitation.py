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
from apps.core.rls import bypass_rls
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
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True)
    with bypass_rls(reason="test_setup.create_establishment"):
        establishment = EstablishmentFactory()
    request_context.set_actor(admin)
    try:
        return create_cohort(establishment=establishment, name="Terminale", school_year="2025-2026")
    finally:
        request_context.clear()


def test_accept_majeur_activates_account():
    cohort = _make_cohort()
    result = import_row(
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
    invitation.refresh_from_db()
    assert invitation.status == StudentImportInvitationStatus.ACCEPTED


def test_accept_mineur_keeps_pending_parental_consent():
    cohort = _make_cohort()
    result = import_row(
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
    result = import_row(
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
    result = import_row(
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
