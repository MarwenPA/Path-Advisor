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
    client.force_authenticate(user=admin)
    return client


def _establishment():
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentFactory()


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
    invitation = CounselorInvitation.objects.get(id=response.json()["id"])
    assert invitation.email == "conseillere@etablissement.test"
    assert invitation.status == CounselorInvitationStatus.PENDING


def test_accept_creates_counselor_account_locked_to_invitation_email():
    establishment = _establishment()
    invitation = create_counselor_invitation(
        establishment=establishment, email="real-counselor@etablissement.test"
    )
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


def test_accept_ignores_body_supplied_email_field():
    """§4.4 anti-pattern guard — no `email` field even accepted by the serializer,
    the account is created from `invitation.email` exclusively."""
    establishment = _establishment()
    invitation = create_counselor_invitation(
        establishment=establishment, email="locked@etablissement.test"
    )
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
    invitation = create_counselor_invitation(
        establishment=establishment, email="p@etablissement.test"
    )
    client = APIClient()

    response = client.post(_accept_url(invitation.token), {}, format="json")

    assert response.status_code == 400
    with bypass_rls(reason="test_assert.no_account"):
        assert not User.objects.filter(email="p@etablissement.test").exists()


def test_accept_with_weak_password_returns_400():
    establishment = _establishment()
    invitation = create_counselor_invitation(
        establishment=establishment, email="p2@etablissement.test"
    )
    client = APIClient()

    response = client.post(_accept_url(invitation.token), {"password": "123"}, format="json")

    assert response.status_code == 400


def test_accept_expired_token_returns_404():
    establishment = _establishment()
    invitation = create_counselor_invitation(
        establishment=establishment, email="p3@etablissement.test"
    )
    invitation.expires_at = timezone.now() - timezone.timedelta(days=1)
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
    invitation = create_counselor_invitation(
        establishment=establishment, email="p4@etablissement.test"
    )
    client = APIClient()
    client.post(_accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json")

    second_response = client.post(
        _accept_url(invitation.token), {"password": "Another-Strong-Pw-2026!"}, format="json"
    )
    assert second_response.status_code == 404


def test_public_status_endpoint_returns_pending():
    establishment = _establishment()
    invitation = create_counselor_invitation(
        establishment=establishment, email="p5@etablissement.test"
    )
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
    invitation = create_counselor_invitation(
        establishment=establishment, email="p6@etablissement.test"
    )
    client = APIClient()
    client.post(_accept_url(invitation.token), {"password": "Path-Advisor-2026!"}, format="json")

    with bypass_rls(reason="test_assert.read_counselor"):
        counselor = User.objects.get(email="p6@etablissement.test")
    assert counselor.requires_mfa is True
    assert counselor.has_mfa_enrolled is False
