"""Story 8.2 — engine, preferences API, tokenized unsubscribe.

The AC3 contract is the heart: after an unsubscribe, `notify()` refuses at
the point of send — proven here end-to-end (unsubscribe via the public
token endpoint, then a notify() call produces no outbox row and no email).
"""

from __future__ import annotations

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.mailer.models import EmailOutbox
from apps.notifications.models import NotificationCategory, NotificationPreference, is_enabled
from apps.notifications.services import notify
from apps.notifications.tokens import make_unsubscribe_token, read_unsubscribe_token

PREFS_URL = "/api/v1/me/notification-preferences/"
UNSUB_URL = "/api/v1/notifications/unsubscribe/"
CAT = NotificationCategory.PROFILE_COMPLETION.value

NOTIFY_KW = {
    "category": CAT,
    "template_app": "notifications",
    "template_base": "email/profile_completion_reminder",
    "context": {
        "first_name": "Sarah",
        "completion_percent": 60,
        "profile_url": "https://path-advisor.fr/profile",
    },
}


@pytest.fixture
def student(db):
    with as_path_admin():
        return User.objects.create_user(
            email="eleve-notif@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )


@pytest.fixture
def client(student):
    c = APIClient()
    c.force_authenticate(user=student)
    return c


# ---------------------------------------------------------------------------
# Engine (AC2 + AC3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_notify_sends_with_legal_footer(student, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        row = notify(user_id=student.id, email=student.email, **NOTIFY_KW)

    assert row is not None
    assert len(mail.outbox) == 1
    html = mail.outbox[0].alternatives[0][0]
    text = mail.outbox[0].body
    # AC2: both legal links, in BOTH bodies (text clients exist).
    for body in (html, text):
        assert "/parametres/notifications" in body
        assert "/desinscription/" in body
    # The unsubscribe link embeds a valid signed token for (user, category).
    token = html.split("/desinscription/")[1].split('"')[0]
    assert read_unsubscribe_token(token) == (student.id, CAT)


@pytest.mark.django_db
def test_notify_refuses_when_opted_out(student):
    NotificationPreference.objects.create(user=student, category=CAT, enabled=False)
    row = notify(user_id=student.id, email=student.email, **NOTIFY_KW)
    # AC3 at the point of send: no outbox row, no email, a normal outcome.
    assert row is None
    assert EmailOutbox.objects.count() == 0


@pytest.mark.django_db
def test_notify_rejects_unknown_category(student):
    with pytest.raises(ValueError, match="Unknown notification category"):
        notify(user_id=student.id, email=student.email, **{**NOTIFY_KW, "category": "spam"})


# ---------------------------------------------------------------------------
# Preferences API (AC1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_lists_all_categories_enabled_by_default(client):
    resp = client.get(PREFS_URL)
    assert resp.status_code == 200
    prefs = resp.json()["preferences"]
    assert {p["category"] for p in prefs} == set(NotificationCategory.values)
    assert all(p["enabled"] for p in prefs)  # opt-out model: no row = enabled


@pytest.mark.django_db
def test_put_upserts_immediately(client, student):
    resp = client.put(PREFS_URL, {"category": CAT, "enabled": False}, format="json")
    assert resp.status_code == 200
    assert is_enabled(student.id, CAT) is False
    # Re-opt-in is an explicit act (AC3) — and works.
    client.put(PREFS_URL, {"category": CAT, "enabled": True}, format="json")
    assert is_enabled(student.id, CAT) is True


@pytest.mark.django_db
def test_put_rejects_garbage(client):
    for payload in ({"category": "spam", "enabled": False}, {"category": CAT, "enabled": "non"}):
        assert client.put(PREFS_URL, payload, format="json").status_code == 400


@pytest.mark.django_db
def test_preferences_require_auth():
    assert APIClient().get(PREFS_URL).status_code in (401, 403)


# ---------------------------------------------------------------------------
# Tokenized unsubscribe (AC3, public)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unsubscribe_via_token_then_engine_refuses(student):
    token = make_unsubscribe_token(student.id, CAT)
    resp = APIClient().post(UNSUB_URL, {"token": token}, format="json")
    assert resp.status_code == 200
    assert resp.json()["category"] == CAT

    assert is_enabled(student.id, CAT) is False
    # End-to-end AC3: the engine now refuses this category for this user.
    assert notify(user_id=student.id, email=student.email, **NOTIFY_KW) is None


@pytest.mark.django_db
def test_unsubscribe_rejects_tampered_token(student):
    token = make_unsubscribe_token(student.id, CAT)
    resp = APIClient().post(UNSUB_URL, {"token": token + "x"}, format="json")
    assert resp.status_code == 400
    assert is_enabled(student.id, CAT) is True  # nothing changed


@pytest.mark.django_db
def test_unsubscribe_is_idempotent(student):
    token = make_unsubscribe_token(student.id, CAT)
    for _ in range(2):
        assert APIClient().post(UNSUB_URL, {"token": token}, format="json").status_code == 200
    assert is_enabled(student.id, CAT) is False
