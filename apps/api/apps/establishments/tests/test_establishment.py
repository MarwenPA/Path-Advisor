"""Story 6.5 §T8.1 — Establishment: creation, unicity UAI, RBAC (AC1)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.establishments.models import Establishment
from apps.establishments.tests.factories import EstablishmentFactory

pytestmark = pytest.mark.django_db


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_establishments_user"):
        return UserFactory(**kwargs)


def _establishments_url() -> str:
    return reverse("establishments:establishment-list-create")


def _payload(**overrides):
    payload = {
        "name": "Lycée Victor Hugo",
        "type": "lycee",
        "city": "Lyon",
        "uai": "0691234A",
        "contact_name": "Karim",
        "contact_email": "karim@lycee.test",
        "license_start": "2026-09-01",
        "license_end": "2027-08-31",
        "license_type": "pilote_gratuit",
    }
    payload.update(overrides)
    return payload


def _admin_client() -> APIClient:
    # `is_superuser=True` bypasses `IsPathAdmin.requires_mfa_verified` in
    # tests (no OTPMiddleware in the DRF test client) — same pattern as
    # `apps.audit.tests.factories.PathAdminUserFactory`.
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


def test_path_admin_can_create_establishment():
    client = _admin_client()
    response = client.post(_establishments_url(), _payload(), format="json")

    assert response.status_code == 201, response.content
    body = response.json()
    assert body["uai"] == "0691234A"
    with bypass_rls(reason="test_assert.read_establishment"):
        assert Establishment.objects.filter(uai="0691234A").exists()


def test_duplicate_uai_returns_409():
    with bypass_rls(reason="test_setup.create_establishment"):
        EstablishmentFactory(uai="0691234A")
    client = _admin_client()

    response = client.post(_establishments_url(), _payload(uai="0691234A"), format="json")

    assert response.status_code == 409, response.content


def test_non_admin_role_is_forbidden():
    student = _uf(role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.post(_establishments_url(), _payload(), format="json")

    assert response.status_code == 403


def test_anonymous_is_forbidden():
    client = APIClient()
    response = client.post(_establishments_url(), _payload(), format="json")
    assert response.status_code in (401, 403)
