"""Story 6.5 §T8.3 — counselor invitation: email-locking, password required,
expired/unknown token → 404, login post-accept triggers requires_mfa (AC4)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import STAFF_ROLES_REQUIRING_MFA, User, UserRole
from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.establishments.models import CounselorInvitation, CounselorInvitationStatus
from apps.establishments.services.counselor_invitation import create_counselor_invitation
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


def _establishment():
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentFactory()


def _invitation(*, establishment, email):
    # Code-review fix (2026-09): `create_counselor_invitation` writes to
    # `counselor_invitations`, RLS-protected (path_admin/bypass only) since
    # migration 0003 — a bare call here (no request, no actor) is denied.
    with bypass_rls(reason="test_setup.create_counselor_invitation"):
        return create_counselor_invitation(establishment=establishment, email=email)


def _accept_url(token: str) -> str:
    return reverse("establishments_auth:counselor-invitation-accept", kwargs={"token": token})


def _status_url(token: str) -> str:
    return reverse("establishments_auth:counselor-invitation-status", kwargs={"token": token})


def test_admin_creates_counselor_invitation():
    establishment = _establishment()
    client = _admin_client()

    response = client.post(
        reverse(
            "establishments:establishment-counselor-list-create",
            kwargs={"establishment_id": establishment.id},
        ),
        {"email": "conseillere@etablissement.test"},
        format="json",
    )

    assert response.status_code == 201, response.content
    with bypass_rls(reason="test_assert.read_counselor_invitation"):
        invitation = CounselorInvitation.objects.get(id=response.json()["id"])
    assert invitation.email == "conseillere@etablissement.test"
    assert invitation.status == CounselorInvitationStatus.PENDING


def test_accept_creates_counselor_account_locked_to_invitation_email():
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="real-counselor@etablissement.test")
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json"
    )

    assert response.status_code == 200, response.content
    with bypass_rls(reason="test_assert.read_counselor"):
        counselor = User.objects.get(email="real-counselor@etablissement.test")
    assert counselor.role == UserRole.COUNSELOR
    assert counselor.tenant_id == establishment.id
    assert counselor.email_verified_at is not None
    assert UserRole.COUNSELOR in STAFF_ROLES_REQUIRING_MFA
    # AC4 — no auto-login: the session must NOT be authenticated after accept.
    assert "sessionid" not in client.cookies or not client.session.get("_auth_user_id")


def test_accept_email_already_registered_returns_409_not_500():
    """Code-review fix (2026-09) — used to raise a raw IntegrityError -> 500."""
    establishment = _establishment()
    _uf(email="deja-inscrit@etablissement.test")
    invitation = _invitation(establishment=establishment, email="deja-inscrit@etablissement.test")
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json"
    )

    assert response.status_code == 409, response.content


def test_accept_ignores_body_supplied_email_field():
    """§4.4 anti-pattern guard — no `email` field even accepted by the serializer,
    the account is created from `invitation.email` exclusively."""
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="locked@etablissement.test")
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token),
        {"email": "attacker@evil.test", "password": "Path-Advisor-2026!"},
        format="json",
    )

    assert response.status_code == 200, response.content
    with bypass_rls(reason="test_assert.no_attacker_account"):
        assert not User.objects.filter(email="attacker@evil.test").exists()
        assert User.objects.filter(email="locked@etablissement.test").exists()


def test_accept_without_password_returns_400():
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="p@etablissement.test")
    client = APIClient()

    response = client.post(_accept_url(invitation.token), {}, format="json")

    assert response.status_code == 400
    with bypass_rls(reason="test_assert.no_account"):
        assert not User.objects.filter(email="p@etablissement.test").exists()


def test_accept_with_weak_password_returns_400():
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="p2@etablissement.test")
    client = APIClient()

    response = client.post(_accept_url(invitation.token), {"password": "123"}, format="json")

    assert response.status_code == 400


def test_accept_expired_token_returns_404():
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="p3@etablissement.test")
    invitation.expires_at = timezone.now() - timezone.timedelta(days=1)
    with bypass_rls(reason="test_setup.expire_invitation"):
        invitation.save(update_fields=["expires_at"])
    client = APIClient()

    response = client.post(
        _accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json"
    )

    assert response.status_code == 404


def test_accept_unknown_token_returns_404():
    client = APIClient()
    response = client.post(
        _accept_url("not-a-real-token"), {"password": "Path-Advisor-2026!"}, format="json"
    )
    assert response.status_code == 404


def test_accept_already_accepted_token_returns_404():
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="p4@etablissement.test")
    client = APIClient()
    client.post(_accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json")

    second_response = client.post(
        _accept_url(invitation.token), {"password": "Another-Strong-Pw-2026!"}, format="json"
    )
    assert second_response.status_code == 404


def test_public_status_endpoint_returns_pending():
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="p5@etablissement.test")
    client = APIClient()

    response = client.get(_status_url(invitation.token))

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_public_status_endpoint_unknown_token_returns_404():
    client = APIClient()
    response = client.get(_status_url("does-not-exist"))
    assert response.status_code == 404


def test_login_after_accept_requires_mfa():
    """AC4 third clause — no new MFA code: `requires_mfa` is already True for
    any `role=counselor` (STAFF_ROLES_REQUIRING_MFA), verified directly on
    the created account (ThrottledLoginView itself is untouched by this story)."""
    establishment = _establishment()
    invitation = _invitation(establishment=establishment, email="p6@etablissement.test")
    client = APIClient()
    client.post(_accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json")

    with bypass_rls(reason="test_assert.read_counselor"):
        counselor = User.objects.get(email="p6@etablissement.test")
    assert counselor.requires_mfa is True
    assert counselor.has_mfa_enrolled is False
