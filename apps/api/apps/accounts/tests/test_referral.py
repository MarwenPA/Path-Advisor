"""Story 10.5 — parrainage : code opaque, attribution au signup, silences.

Contrats : le code est créé au premier accès et stable ; l'inscription avec
un code valide crée l'attribution + notifie le parrain (email + push, sans
identité du filleul) ; un code invalide ou l'auto-parrainage sont ignorés
en silence (pas d'oracle) ; l'export RGPD porte le code, jamais les
filleuls.
"""

from __future__ import annotations

import json
from unittest import mock

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Referral, ReferralCode, User, UserRole, UserStatus
from apps.core.rls import bypass_rls

pytestmark = pytest.mark.django_db

REFERRAL_URL = "/api/v1/auth/referral/"
SIGNUP_URL = "/api/v1/auth/registration/"


def _student(email: str) -> User:
    with bypass_rls(reason="test_setup.create_referral_user"):
        return User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )


def _signup(payload_extra: dict, capture) -> object:
    client = APIClient()
    with capture(execute=True):
        return client.post(
            SIGNUP_URL,
            {
                "email": "filleul@test.local",
                "password1": "Correct-Horse-42!",
                "password2": "Correct-Horse-42!",
                "birth_date": "2007-03-01",  # majeur de 15 ans — pas de branche parentale
                "consent_rgpd_accepted": True,
                "consent_cgu_version": "1.0",
                **payload_extra,
            },
            format="json",
        )


def test_referral_endpoint_creates_stable_opaque_code():
    student = _student("parrain@test.local")
    client = APIClient()
    client.force_authenticate(user=student)

    first = client.get(REFERRAL_URL)
    assert first.status_code == 200
    body = first.json()
    assert body["referred_count"] == 0
    assert body["url"].endswith(f"/r/{body['code']}")
    # Opaque : jamais l'usr_ id dans le lien partageable.
    assert student.id not in body["url"]

    second = client.get(REFERRAL_URL).json()
    assert second["code"] == body["code"]  # stable


def test_signup_with_valid_code_attributes_and_notifies(
    django_capture_on_commit_callbacks,
):
    referrer = _student("parrain-2@test.local")
    with bypass_rls(reason="test_setup.create_code"):
        code = ReferralCode.objects.create(user=referrer).code

    with mock.patch("apps.notifications.tasks.send_web_push.delay") as push:
        response = _signup({"referral_code": code}, django_capture_on_commit_callbacks)

    assert response.status_code == 201, response.content
    with bypass_rls(reason="test.read_referral"):
        referral = Referral.objects.get(referrer=referrer)
        assert referral.referee.email == "filleul@test.local"

    referrer_mails = [m for m in mail.outbox if m.to == [referrer.email]]
    assert len(referrer_mails) == 1
    assert "grâce à ton" in referrer_mails[0].body
    # Jamais l'identité du filleul, ni dans l'email ni dans le push.
    assert "filleul@test.local" not in referrer_mails[0].body
    push_payload = push.call_args.args[2]
    assert push_payload["title"] == "Ton pote vient de rejoindre Path-Advisor"
    assert "filleul" not in push_payload["body"]


def test_signup_with_unknown_code_is_silently_ignored(django_capture_on_commit_callbacks):
    response = _signup({"referral_code": "code-inconnu"}, django_capture_on_commit_callbacks)
    assert response.status_code == 201, response.content
    with bypass_rls(reason="test.read_referral"):
        assert not Referral.objects.exists()


def test_referral_endpoint_counts_and_requires_student(django_capture_on_commit_callbacks):
    referrer = _student("parrain-3@test.local")
    with bypass_rls(reason="test_setup.create_code"):
        code = ReferralCode.objects.create(user=referrer).code
    _signup({"referral_code": code}, django_capture_on_commit_callbacks)

    client = APIClient()
    client.force_authenticate(user=referrer)
    assert client.get(REFERRAL_URL).json()["referred_count"] == 1

    anon = APIClient()
    assert anon.get(REFERRAL_URL).status_code in (401, 403)


def test_gdpr_export_carries_code_never_referees(django_capture_on_commit_callbacks):
    from apps.accounts.exporters.accounts import export_account_profile

    referrer = _student("parrain-4@test.local")
    with bypass_rls(reason="test_setup.create_code"):
        code = ReferralCode.objects.create(user=referrer).code
    _signup({"referral_code": code}, django_capture_on_commit_callbacks)

    with bypass_rls(reason="test.export"):
        entry = next(iter(export_account_profile(referrer)))
        payload = json.loads(entry.content)
        assert payload["referral"] == {
            "code": code,
            "referred_count": 1,
            "was_referred": False,
        }
        assert "filleul@test.local" not in entry.content.decode()

        referee = User.objects.get(email="filleul@test.local")
        referee_payload = json.loads(next(iter(export_account_profile(referee))).content)
        assert referee_payload["referral"]["was_referred"] is True
        # Le filleul ne voit pas QUI l'a parrainé (la donnée du parrain).
        assert code not in json.dumps(referee_payload)


def test_referee_account_deletion_cascades_attribution(django_capture_on_commit_callbacks):
    referrer = _student("parrain-5@test.local")
    with bypass_rls(reason="test_setup.create_code"):
        code = ReferralCode.objects.create(user=referrer).code
    _signup({"referral_code": code}, django_capture_on_commit_callbacks)

    with bypass_rls(reason="test.delete_referee"):
        User.objects.get(email="filleul@test.local").delete()
        assert not Referral.objects.filter(referrer=referrer).exists()
