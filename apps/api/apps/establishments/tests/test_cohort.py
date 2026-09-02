"""Story 6.5 §T8.1 — Cohort: creation, tenant_id denormalization, RBAC (AC2)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.establishments.models import Cohort
from apps.establishments.tests.factories import EstablishmentFactory

pytestmark = pytest.mark.django_db


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_establishments_user"):
        return UserFactory(**kwargs)


def _admin_client():
    admin = _uf(role=UserRole.PATH_ADMIN, is_superuser=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


def _cohorts_url(establishment_id) -> str:
    return reverse(
        "establishments:establishment-cohort-list-create",
        kwargs={"establishment_id": establishment_id},
    )


def test_creates_cohort_with_tenant_id_from_establishment():
    with bypass_rls(reason="test_setup.create_establishment"):
        establishment = EstablishmentFactory()
    client = _admin_client()

    response = client.post(
        _cohorts_url(establishment.id),
        {"name": "Terminale 2025-2026", "school_year": "2025-2026"},
        format="json",
    )

    assert response.status_code == 201, response.content
    cohort = Cohort.objects.get(id=response.json()["id"])
    assert cohort.tenant_id == establishment.id
    assert cohort.establishment_id == establishment.id


def test_unknown_establishment_returns_404():
    import uuid

    client = _admin_client()
    response = client.post(
        _cohorts_url(uuid.uuid4()),
        {"name": "Terminale", "school_year": "2025-2026"},
        format="json",
    )
    assert response.status_code == 404


def test_non_admin_role_is_forbidden():
    with bypass_rls(reason="test_setup.create_establishment"):
        establishment = EstablishmentFactory()
    student = _uf(role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.post(
        _cohorts_url(establishment.id),
        {"name": "Terminale", "school_year": "2025-2026"},
        format="json",
    )
    assert response.status_code == 403
