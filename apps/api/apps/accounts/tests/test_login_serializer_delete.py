"""DELETED-status users get a typed 403 at login (Story 1.12 §AC3, §T6)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def test_login_rejects_deleted_user_with_403(api_client):
    user = UserFactory(email="alice@example.test")
    user.status = UserStatus.DELETED
    user.is_active = False
    user.save(update_fields=["status", "is_active"])

    res = api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code == 403, res.content
    body = res.json()
    assert body["type"].endswith("/account-deleted")
    assert "désactivé" in body["detail"].lower() or "supprimé" in body["title"].lower()


def test_login_unknown_email_does_not_leak_400(api_client):
    # Sanity: same email format, no user — the standard 4xx/dj-rest-auth path,
    # NOT the AccountDeleted 403.
    res = api_client.post(
        reverse("rest_login"),
        {"email": "ghost@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code in (400, 401)
    body = res.json()
    assert "account-deleted" not in body.get("type", "")


def test_login_active_user_unaffected(api_client):
    UserFactory(email="bob@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": "bob@example.test", "password": _PWD},
        format="json",
    )
    # 200 if email_verified, 400 if not (depends on dj-rest-auth verification flow).
    # Either way, NOT 403 / account-deleted.
    assert res.status_code != 403
    body = res.json() if res.status_code != 200 else {}
    assert "account-deleted" not in body.get("type", "")
