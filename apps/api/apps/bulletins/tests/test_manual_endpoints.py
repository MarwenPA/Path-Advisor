"""Tests for Story 2.4 — POST + PATCH /api/v1/students/me/bulletins/manual."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserStatus
from apps.students.models import StudentProfile


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="sarah@test.local",
        password="Strong1!pass",  # noqa: S106
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def profile(user):
    return StudentProfile.objects.create(
        user=user,
        onboarding_step1_status="completed",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


_VALID_MATIERES = [
    {"subject_id": "mathematiques", "note": 14.5, "appreciation": None},
    {"subject_id": "svt", "note": 13.0, "appreciation": "Bonne progression"},
]

_PAYLOAD = {
    "trimestre_label": "Trim. 1",
    "year": "2025-2026",
    "level_at_save": "lycee_terminale",
    "subjects_ref_version": "2026-06-v1",
    "matieres": _VALID_MATIERES,
}


class TestPostManualBulletin:
    def test_create_bulletin_returns_201(self, auth_client, profile):
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), _PAYLOAD, format="json"
        )
        assert response.status_code == 201

    def test_create_bulletin_response_shape(self, auth_client, profile):
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), _PAYLOAD, format="json"
        )
        data = response.json()
        assert "id" in data
        assert data["source"] == "manual"
        assert data["trimestre_label"] == "Trim. 1"

    def test_create_with_zero_matieres_returns_422(self, auth_client, profile):
        payload = {**_PAYLOAD, "matieres": []}
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), payload, format="json"
        )
        assert response.status_code == 422

    def test_note_above_20_returns_400(self, auth_client, profile):
        payload = {
            **_PAYLOAD,
            "matieres": [{"subject_id": "mathematiques", "note": 21.0, "appreciation": None}],
        }
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), payload, format="json"
        )
        assert response.status_code == 400

    def test_note_below_0_returns_400(self, auth_client, profile):
        payload = {
            **_PAYLOAD,
            "matieres": [{"subject_id": "mathematiques", "note": -1.0, "appreciation": None}],
        }
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), payload, format="json"
        )
        assert response.status_code == 400

    def test_custom_subject_with_prefix_is_accepted(self, auth_client, profile):
        payload = {
            **_PAYLOAD,
            "matieres": [
                {"subject_id": "custom:latin", "note": 14.0, "appreciation": None, "is_custom": True}
            ],
        }
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), payload, format="json"
        )
        assert response.status_code == 201

    def test_unauthenticated_returns_401(self, profile):
        client = APIClient()
        response = client.post(
            reverse("bulletins:me-bulletins-manual"), _PAYLOAD, format="json"
        )
        assert response.status_code == 401

    def test_appreciation_over_500_chars_returns_400(self, auth_client, profile):
        payload = {
            **_PAYLOAD,
            "matieres": [
                {
                    "subject_id": "mathematiques",
                    "note": 14.5,
                    "appreciation": "x" * 501,
                }
            ],
        }
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), payload, format="json"
        )
        assert response.status_code == 400


class TestPatchManualBulletin:
    @pytest.fixture
    def bulletin_id(self, auth_client, profile):
        response = auth_client.post(
            reverse("bulletins:me-bulletins-manual"), _PAYLOAD, format="json"
        )
        assert response.status_code == 201
        return response.json()["id"]

    def test_patch_updates_note(self, auth_client, profile, bulletin_id):
        patch_payload = {
            "matieres": [
                {"subject_id": "mathematiques", "note": 15.0, "appreciation": None}
            ]
        }
        response = auth_client.patch(
            reverse("bulletins:me-bulletins-manual-detail", kwargs={"pk": bulletin_id}),
            patch_payload,
            format="json",
        )
        assert response.status_code == 200

    def test_patch_with_invalid_note_returns_400(self, auth_client, profile, bulletin_id):
        response = auth_client.patch(
            reverse("bulletins:me-bulletins-manual-detail", kwargs={"pk": bulletin_id}),
            {"matieres": [{"subject_id": "mathematiques", "note": 25.0, "appreciation": None}]},
            format="json",
        )
        assert response.status_code == 400

    def test_patch_other_users_bulletin_returns_404(self, profile, bulletin_id):
        other_user = User.objects.create_user(
            email="other@test.local",
            password="Strong1!pass",  # noqa: S106
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)
        response = other_client.patch(
            reverse("bulletins:me-bulletins-manual-detail", kwargs={"pk": bulletin_id}),
            {"matieres": _VALID_MATIERES},
            format="json",
        )
        assert response.status_code == 404
