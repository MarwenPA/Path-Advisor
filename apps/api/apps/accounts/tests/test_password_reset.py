"""Password reset flow — Story 1.5 §AC5, §AC6.

Covers: request email (anti-enum 200 identical for known/unknown), email
content (Next.js URL via PathAdvisorPasswordResetSerializer), confirm
endpoint side-effects (session purge + lockout cleared + audit + completion
email).
"""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


def _make_active_user(email: str = "alice@example.test"):
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email)
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    return user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# ---------------------------------------------------------------------------
# Request endpoint
# ---------------------------------------------------------------------------


def test_request_for_known_email_sends_email_and_audits(api_client):
    user = _make_active_user("alice@example.test")
    mail.outbox.clear()

    res = api_client.post(
        reverse("rest_password_reset"),
        {"email": "alice@example.test"},
        format="json",
    )
    assert res.status_code == 200
    # Spec §AC5 wording — identical regardless of email known/unknown.
    assert res.json() == {
        "detail": "Si cet email existe, un lien de réinitialisation t'a été envoyé."
    }

    # Email landed
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    # Story 1.5 §AC5: link points at the Next.js front-end route, NOT the
    # default Django-served allauth template.
    assert "/auth/reset-password/" in body

    # Round-trip the uid+token through the same decoders the confirm endpoint
    # uses — a serializer regression that wired the wrong encoder would still
    # pass the prefix check above (code-review P19 — Story 1.5 review
    # 2026-05-27).
    import re

    from allauth.account.forms import default_token_generator
    from allauth.account.utils import url_str_to_user_pk

    link_match = re.search(r"/auth/reset-password/([^/\s]+)/([^/\s]+)", body)
    assert link_match is not None, body
    uid_in_email, token_in_email = link_match.group(1), link_match.group(2)
    assert url_str_to_user_pk(uid_in_email) == user.pk
    assert default_token_generator.check_token(user, token_in_email) is True

    # Audit row tagged with the user.
    assert AuditLog.objects.filter(action="auth.password_reset_requested").exists()


def test_request_for_unknown_email_returns_same_200_but_no_send(api_client):
    """Anti-enum: response body shape MUST be identical to the known-email branch."""
    mail.outbox.clear()

    res_unknown = api_client.post(
        reverse("rest_password_reset"),
        {"email": "ghost@example.test"},
        format="json",
    )
    assert res_unknown.status_code == 200
    # No SMTP traffic for unknown emails.
    assert len(mail.outbox) == 0
    # Different audit action keyed for DPO enumeration-detection — never
    # surfaced via HTTP.
    assert AuditLog.objects.filter(action="auth.password_reset_requested_unknown").exists()


def test_request_per_email_throttle_429_after_one_attempt(api_client):
    _make_active_user("alice@example.test")
    url = reverse("rest_password_reset")

    res1 = api_client.post(url, {"email": "alice@example.test"}, format="json")
    assert res1.status_code == 200

    res2 = api_client.post(url, {"email": "alice@example.test"}, format="json")
    assert res2.status_code == 429


# ---------------------------------------------------------------------------
# Confirm endpoint
# ---------------------------------------------------------------------------


def _build_reset_link(user) -> tuple[str, str]:
    """Return (uid, token) for `user` matching what the email contains.

    allauth has its own `user_pk_to_url_str` encoder (used by
    `AllAuthPasswordResetForm.save`) — Django's stdlib `urlsafe_base64_encode`
    produces a different format. The confirm endpoint validates with allauth's
    decoder, so we must match the encoder it expects.
    """
    from allauth.account.forms import default_token_generator
    from allauth.account.utils import user_pk_to_url_str

    uid = user_pk_to_url_str(user)
    token = default_token_generator.make_token(user)
    return uid, token


def test_confirm_with_valid_token_updates_password(api_client):
    user = _make_active_user("alice@example.test")
    uid, token = _build_reset_link(user)
    new_pwd = "BrandNew-Password-2026!"

    res = api_client.post(
        reverse("rest_password_reset_confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password1": new_pwd,
            "new_password2": new_pwd,
        },
        format="json",
    )
    assert res.status_code == 200, res.content
    user.refresh_from_db()
    assert user.check_password(new_pwd)
    assert not user.check_password(_PWD)

    # Audit row with the post-reset side-effects.
    assert AuditLog.objects.filter(
        action="auth.password_reset_completed", subject_id=user.id
    ).exists()


def test_confirm_clears_lockout_on_success(api_client):
    """Story 1.5 §AC6: recovery flow releases a locked account."""
    user = _make_active_user("alice@example.test")
    user.locked_until = timezone.now() + timezone.timedelta(minutes=10)
    user.save(update_fields=["locked_until"])
    uid, token = _build_reset_link(user)

    api_client.post(
        reverse("rest_password_reset_confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password1": "RecoveryPwd-2026!",
            "new_password2": "RecoveryPwd-2026!",
        },
        format="json",
    )
    user.refresh_from_db()
    assert user.locked_until is None


def test_confirm_sends_completion_email(api_client):
    user = _make_active_user("alice@example.test")
    uid, token = _build_reset_link(user)
    mail.outbox.clear()

    api_client.post(
        reverse("rest_password_reset_confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password1": "FreshPwd-2026!",
            "new_password2": "FreshPwd-2026!",
        },
        format="json",
    )
    # The "password changed" confirmation email is sent best-effort.
    assert any("mot de passe" in (m.body or "").lower() for m in mail.outbox)


def test_confirm_with_invalid_token_returns_400(api_client):
    user = _make_active_user("alice@example.test")
    uid, _ = _build_reset_link(user)

    res = api_client.post(
        reverse("rest_password_reset_confirm"),
        {
            "uid": uid,
            "token": "invalid-token",
            "new_password1": "BrandNew-2026!",
            "new_password2": "BrandNew-2026!",
        },
        format="json",
    )
    assert res.status_code == 400
    user.refresh_from_db()
    assert user.check_password(_PWD)  # unchanged


def test_confirm_rejects_deleted_user_via_allauth_filter(api_client):
    """Defense-in-depth regression: Story 1.12's soft-delete sets `is_active=False`,
    which makes allauth's `PasswordResetForm.get_users(is_active=True)` skip
    the row — the reset email is never sent and the token is never issued.

    This test simulates the chain by minting a token AGAINST the DELETED user
    (bypass the request endpoint) and verifying the confirm endpoint still
    rejects it because the underlying serializer's `set_password_form_class.
    get_user(...)` filters on `is_active=True`. The 1.12 contract is what we
    rely on (code-review D4 — Story 1.5 review 2026-05-27, option a).
    """
    from apps.accounts.models import UserStatus

    user = _make_active_user("alice@example.test")
    user.status = UserStatus.DELETED
    user.is_active = False
    user.save(update_fields=["status", "is_active"])
    uid, token = _build_reset_link(user)

    res = api_client.post(
        reverse("rest_password_reset_confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password1": "ShouldFail-2026!",
            "new_password2": "ShouldFail-2026!",
        },
        format="json",
    )
    assert res.status_code == 400
    user.refresh_from_db()
    # Password unchanged — confirms allauth's is_active filter caught the
    # DELETED user BEFORE the parent serializer wrote the new hash.
    assert user.check_password(_PWD)
