"""Story 10.2 — Web Push : opt-in/out API, fan-out engine, délivrance.

Contrats clés : le POST/DELETE d'abonnement est scopé au user courant, le
`push=` de `notify()` s'enfile UNIQUEMENT après commit et derrière la même
porte opt-out que l'email, et la délivrance purge les souscriptions
révoquées (404/410) sans jamais relancer un push raté (l'email est le canal
durable).
"""

from __future__ import annotations

from unittest import mock

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.notifications.models import (
    NotificationCategory,
    NotificationPreference,
    PushSubscription,
)
from apps.notifications.push import deliver_web_push
from apps.notifications.services import notify

SUBS_URL = "/api/v1/me/push-subscriptions/"
VAPID_URL = "/api/v1/notifications/push/vapid-public-key/"
CAT = NotificationCategory.SCHOOL_RESPONSES.value

SUB_PAYLOAD = {
    "endpoint": "https://push.example.test/send/abc123",
    "keys": {"p256dh": "BPubKeyFake", "auth": "authFake"},
}


@pytest.fixture
def student(db):
    with as_path_admin():
        return User.objects.create_user(
            email="eleve-push@test.local",
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


# ─── API opt-in / opt-out ─────────────────────────────────────────────────────


def test_subscribe_creates_row_and_is_idempotent(client, student):
    r = client.post(SUBS_URL, SUB_PAYLOAD, format="json")
    assert r.status_code == 201
    r = client.post(SUBS_URL, SUB_PAYLOAD, format="json")
    assert r.status_code == 200  # update in place, pas de doublon
    with as_path_admin():
        assert PushSubscription.objects.filter(user=student).count() == 1


def test_subscribe_reassigns_endpoint_on_account_switch(client, student, db):
    client.post(SUBS_URL, SUB_PAYLOAD, format="json")
    with as_path_admin():
        other = User.objects.create_user(
            email="eleve-push-2@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    c2 = APIClient()
    c2.force_authenticate(user=other)
    c2.post(SUBS_URL, SUB_PAYLOAD, format="json")
    with as_path_admin():
        sub = PushSubscription.objects.get(endpoint=SUB_PAYLOAD["endpoint"])
        assert sub.user_id == other.id


def test_unsubscribe_deletes_and_is_idempotent(client, student):
    client.post(SUBS_URL, SUB_PAYLOAD, format="json")
    r = client.delete(SUBS_URL, {"endpoint": SUB_PAYLOAD["endpoint"]}, format="json")
    assert r.status_code == 204
    r = client.delete(SUBS_URL, {"endpoint": SUB_PAYLOAD["endpoint"]}, format="json")
    assert r.status_code == 204
    with as_path_admin():
        assert not PushSubscription.objects.filter(user=student).exists()


def test_endpoints_require_auth(db):
    anon = APIClient()
    assert anon.post(SUBS_URL, SUB_PAYLOAD, format="json").status_code in (401, 403)
    assert anon.get(VAPID_URL).status_code in (401, 403)


def test_vapid_key_204_when_unconfigured_200_when_set(client, settings):
    settings.WEBPUSH_VAPID_PUBLIC_KEY = ""
    assert client.get(VAPID_URL).status_code == 204
    settings.WEBPUSH_VAPID_PUBLIC_KEY = "BFakePublicKey"
    r = client.get(VAPID_URL)
    assert r.status_code == 200 and r.json()["public_key"] == "BFakePublicKey"


# ─── Fan-out engine (notify → task, on_commit, porte opt-out) ─────────────────

NOTIFY_KW = {
    "category": CAT,
    "template_app": "outreach",
    "template_base": "email/school_responded",
    "context": {
        "school": {"name": "Lycée X"},
        "outreach": {"id": "eor_1", "profession": {"name": "Technicien"}},
        "response": {"action": "interested", "comment": ""},
        "response_url": "http://localhost:3000/mes-envois/eor_1",
        "explore_url": "http://localhost:3000/schools",
    },
}
PUSH = {"title": "Une école t'a répondu", "body": "Ta réponse t'attend.", "url": "http://x/y"}


def test_notify_enqueues_push_on_commit(student, django_capture_on_commit_callbacks):
    with (
        mock.patch("apps.notifications.tasks.send_web_push.delay") as delay,
        django_capture_on_commit_callbacks(execute=True),
    ):
        notify(user_id=student.id, email=student.email, push=PUSH, **NOTIFY_KW)
    delay.assert_called_once_with(student.id, CAT, PUSH)


def test_notify_without_push_enqueues_nothing(student, django_capture_on_commit_callbacks):
    with (
        mock.patch("apps.notifications.tasks.send_web_push.delay") as delay,
        django_capture_on_commit_callbacks(execute=True),
    ):
        notify(user_id=student.id, email=student.email, **NOTIFY_KW)
    delay.assert_not_called()


def test_notify_opted_out_sends_neither_email_nor_push(student, django_capture_on_commit_callbacks):
    with as_path_admin():
        NotificationPreference.objects.create(user=student, category=CAT, enabled=False)
    with (
        mock.patch("apps.notifications.tasks.send_web_push.delay") as delay,
        django_capture_on_commit_callbacks(execute=True),
    ):
        row = notify(user_id=student.id, email=student.email, push=PUSH, **NOTIFY_KW)
    assert row is None
    delay.assert_not_called()


# ─── Délivrance (pywebpush mocké) ────────────────────────────────────────────


def _make_sub(student, endpoint="https://push.example.test/send/a"):
    with as_path_admin():
        return PushSubscription.objects.create(
            user=student, endpoint=endpoint, p256dh="BPub", auth="auth"
        )


def _exc_with_status(code):
    from pywebpush import WebPushException

    response = mock.Mock(status_code=code)
    return WebPushException("boom", response=response)


def test_deliver_sends_to_every_subscription(student, settings):
    settings.WEBPUSH_VAPID_PRIVATE_KEY = "fake-priv"
    _make_sub(student, "https://push.example.test/send/a")
    _make_sub(student, "https://push.example.test/send/b")
    with as_path_admin(), mock.patch("apps.notifications.push.webpush") as wp:
        result = deliver_web_push(user_id=student.id, category=CAT, payload=PUSH)
    assert result == {"sent": 2, "purged": 0, "failed": 0}
    assert wp.call_count == 2
    ttl = wp.call_args.kwargs["ttl"]
    assert ttl == 86_400


def test_deliver_purges_revoked_subscription_on_410(student, settings):
    settings.WEBPUSH_VAPID_PRIVATE_KEY = "fake-priv"
    _make_sub(student)
    with (
        as_path_admin(),
        mock.patch("apps.notifications.push.webpush", side_effect=_exc_with_status(410)),
    ):
        result = deliver_web_push(user_id=student.id, category=CAT, payload=PUSH)
    assert result == {"sent": 0, "purged": 1, "failed": 0}
    with as_path_admin():
        assert not PushSubscription.objects.filter(user=student).exists()


def test_deliver_logs_but_never_raises_on_other_errors(student, settings):
    settings.WEBPUSH_VAPID_PRIVATE_KEY = "fake-priv"
    _make_sub(student)
    with (
        as_path_admin(),
        mock.patch("apps.notifications.push.webpush", side_effect=_exc_with_status(500)),
    ):
        result = deliver_web_push(user_id=student.id, category=CAT, payload=PUSH)
    assert result == {"sent": 0, "purged": 0, "failed": 1}
    with as_path_admin():
        assert PushSubscription.objects.filter(user=student).exists()  # pas purgée


def test_deliver_rechecks_opt_out_at_delivery_time(student, settings):
    settings.WEBPUSH_VAPID_PRIVATE_KEY = "fake-priv"
    _make_sub(student)
    with as_path_admin():
        NotificationPreference.objects.create(user=student, category=CAT, enabled=False)
    with as_path_admin(), mock.patch("apps.notifications.push.webpush") as wp:
        result = deliver_web_push(user_id=student.id, category=CAT, payload=PUSH)
    assert result == {"sent": 0, "purged": 0, "failed": 0}
    wp.assert_not_called()


def test_deliver_noop_when_unconfigured(student, settings):
    settings.WEBPUSH_VAPID_PRIVATE_KEY = ""
    _make_sub(student)
    with as_path_admin(), mock.patch("apps.notifications.push.webpush") as wp:
        result = deliver_web_push(user_id=student.id, category=CAT, payload=PUSH)
    assert result == {"sent": 0, "purged": 0, "failed": 0}
    wp.assert_not_called()


def test_deliver_graceful_without_subscriptions(student, settings):
    settings.WEBPUSH_VAPID_PRIVATE_KEY = "fake-priv"
    with as_path_admin(), mock.patch("apps.notifications.push.webpush") as wp:
        result = deliver_web_push(user_id=student.id, category=CAT, payload=PUSH)
    assert result == {"sent": 0, "purged": 0, "failed": 0}
    wp.assert_not_called()


# ─── Export RGPD ─────────────────────────────────────────────────────────────


def test_gdpr_export_includes_push_subscriptions(student):
    import json

    from apps.notifications.exporters import export_notifications

    _make_sub(student)
    with as_path_admin():
        entry = next(iter(export_notifications(student)))
    payload = json.loads(entry.content)
    assert payload["push_subscriptions"][0]["endpoint"] == "https://push.example.test/send/a"
