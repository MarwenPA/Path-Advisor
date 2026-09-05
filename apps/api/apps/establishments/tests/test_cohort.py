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
    with bypass_rls(reason="test_assert.read_cohort"):
        cohort = Cohort.objects.get(id=response.json()["id"])
    assert cohort.tenant_id == establishment.id
    assert cohort.establishment_id == establishment.id


def test_duplicate_cohort_name_returns_409_not_500():
    """Code-review fix (2026-09) — migration 0004's uniqueness constraint on
    (establishment, name, school_year); used to be a raw IntegrityError."""
    with bypass_rls(reason="test_setup.create_establishment"):
        establishment = EstablishmentFactory()
    client = _admin_client()
    payload = {"name": "Terminale 2025-2026", "school_year": "2025-2026"}

    first = client.post(_cohorts_url(establishment.id), payload, format="json")
    assert first.status_code == 201, first.content

    second = client.post(_cohorts_url(establishment.id), payload, format="json")
    assert second.status_code == 409, second.content


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
