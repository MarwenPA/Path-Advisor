"""Integration tests for the onboarding step-1 endpoints (Story 2.1 AC5, AC6, AC10).

Run on SQLite (fast path). RLS isolation is exercised in `test_rls.py`
against PostgreSQL.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.students.models import OnboardingStep1Status, StudentProfile

User = get_user_model()


@pytest.fixture
def user(db):
    # Pass 1 review H1 — endpoints now gate behind
    # `IsAuthenticatedAndActive + IsStudent`. The default User created by
    # `create_user` ships as `email_unverified` / `email_verified_at=None`,
    # which makes `is_fully_active` False. Onboarding step-1 is reached
    # AFTER email verification in the real flow, so the fixture mirrors that
    # post-verification state — student role (the model default) + ACTIVE
    # status + a non-null `email_verified_at`.
    from django.utils import timezone

    return User.objects.create_user(
        email="sarah@test.local",
        password="Strong1!password",
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def parent_user(db):
    """Used by the H1 RBAC tests — a non-student authenticated user that must
    be refused by the endpoint even though they're fully active."""
    from django.utils import timezone

    from apps.accounts.models import UserRole

    return User.objects.create_user(
        email="parent@test.local",
        password="Strong1!password",
        role=UserRole.PARENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def anon_client():
    return APIClient()


URL = "/api/v1/students/me/onboarding/passions"


# --- GET --------------------------------------------------------------------


@pytest.mark.django_db
class TestRbac:
    """Pass 1 review H1 — non-student authenticated users must be refused."""

    def test_parent_role_is_refused(self, parent_user):
        api = APIClient()
        api.force_authenticate(user=parent_user)
        resp = api.get(URL)
        assert resp.status_code == 403, resp.content

    def test_parent_role_cannot_patch(self, parent_user):
        api = APIClient()
        api.force_authenticate(user=parent_user)
        resp = api.patch(URL, data={"step": "skip"}, format="json")
        assert resp.status_code == 403, resp.content


@pytest.mark.django_db
class TestGet:
    def test_unauthenticated_403(self, anon_client):
        # DRF returns 403 by default for unauthenticated, 401 only with explicit
        # WWW-Authenticate setup. Matches the rest of the project's auth shape.
        resp = anon_client.get(URL)
        assert resp.status_code in (401, 403)

    def test_returns_empty_defaults_when_no_profile(self, client):
        resp = client.get(URL)
        assert resp.status_code == 200
        assert resp.data == {
            "passions": [],
            "valeurs": [],
            "interets": {"1": None, "2": None, "3": None},
            "onboarding_step1_status": "pending",
            "onboarding_step1_completed_at": None,
        }

    def test_returns_existing_profile(self, client, user):
        StudentProfile.objects.create(
            user=user,
            passions=["sciences-nature", "musique", "tech-code"],
            valeurs=["justice-sociale", "creativite", "sens-utilite"],
            onboarding_step1_status=OnboardingStep1Status.IN_PROGRESS,
        )
        resp = client.get(URL)
        assert resp.status_code == 200
        assert resp.data["passions"] == ["sciences-nature", "musique", "tech-code"]
        assert resp.data["valeurs"] == ["justice-sociale", "creativite", "sens-utilite"]
        assert resp.data["onboarding_step1_status"] == "in_progress"

    def test_does_not_create_profile_on_get(self, client):
        # AC5 — first-load reads return defaults; the row is created only on PATCH.
        client.get(URL)
        assert not StudentProfile.objects.exists()


# --- PATCH passions --------------------------------------------------------


@pytest.mark.django_db
class TestPatchPassions:
    def test_creates_profile_on_first_patch(self, client, user):
        resp = client.patch(
            URL,
            data={"step": "passions", "passions": ["sciences-nature", "musique", "tech-code"]},
            format="json",
        )
        assert resp.status_code == 200, resp.content
        assert StudentProfile.objects.filter(user=user).exists()

    def test_persists_passions(self, client, user):
        client.patch(
            URL,
            data={"step": "passions", "passions": ["sciences-nature", "musique", "tech-code"]},
            format="json",
        )
        p = StudentProfile.objects.get(user=user)
        assert p.passions == ["sciences-nature", "musique", "tech-code"]
        assert p.onboarding_step1_status == OnboardingStep1Status.IN_PROGRESS

    def test_accepts_8_passions_max(self, client, user):
        eight = [
            "sciences-nature", "tech-code", "arts-creation", "sport-corps",
            "musique", "cinema-series", "lecture-ecriture", "voyage-cultures",
        ]
        resp = client.patch(URL, data={"step": "passions", "passions": eight}, format="json")
        assert resp.status_code == 200, resp.content

    def test_rejects_9_passions(self, client, user):
        nine = [
            "sciences-nature", "tech-code", "arts-creation", "sport-corps",
            "musique", "cinema-series", "lecture-ecriture", "voyage-cultures",
            "cuisine",
        ]
        resp = client.patch(URL, data={"step": "passions", "passions": nine}, format="json")
        assert resp.status_code == 400

    def test_rejects_unknown_id(self, client, user):
        resp = client.patch(
            URL,
            data={"step": "passions", "passions": ["sciences-nature", "musique", "bogus-id"]},
            format="json",
        )
        assert resp.status_code == 400

    def test_accepts_custom_passion(self, client, user):
        resp = client.patch(
            URL,
            data={
                "step": "passions",
                "passions": ["sciences-nature", "musique", "custom:graphql"],
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content

    def test_rejects_malformed_custom(self, client, user):
        resp = client.patch(
            URL,
            data={
                "step": "passions",
                "passions": ["sciences-nature", "musique", "custom:Bad Slug"],
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_rejects_mixed_step_fields(self, client, user):
        """AC5 — a single PATCH carries one sub-step's data only."""
        resp = client.patch(
            URL,
            data={
                "step": "passions",
                "passions": ["sciences-nature", "musique", "tech-code"],
                "valeurs": ["justice-sociale", "creativite", "sens-utilite"],
            },
            format="json",
        )
        assert resp.status_code == 400


# --- PATCH valeurs ---------------------------------------------------------


@pytest.mark.django_db
class TestPatchValeurs:
    def test_persists_valeurs(self, client, user):
        client.patch(
            URL,
            data={"step": "valeurs", "valeurs": ["justice-sociale", "creativite", "sens-utilite"]},
            format="json",
        )
        p = StudentProfile.objects.get(user=user)
        assert p.valeurs == ["justice-sociale", "creativite", "sens-utilite"]

    def test_rejects_6_valeurs(self, client, user):
        six = [
            "justice-sociale", "creativite", "sens-utilite", "aventure", "defi", "apprendre",
        ]
        resp = client.patch(URL, data={"step": "valeurs", "valeurs": six}, format="json")
        assert resp.status_code == 400

    def test_rejects_custom_valeur(self, client, user):
        # Valeurs do NOT accept custom: prefix (referential is fixed at MVP).
        resp = client.patch(
            URL,
            data={
                "step": "valeurs",
                "valeurs": ["justice-sociale", "creativite", "custom:patience"],
            },
            format="json",
        )
        assert resp.status_code == 400


# --- PATCH interets --------------------------------------------------------


@pytest.mark.django_db
class TestPatchInterets:
    # Helper: seed the canonical "complete prerequisites" state in one call.
    @staticmethod
    def _seed_passions_and_valeurs(user):
        StudentProfile.objects.create(
            user=user,
            passions=["sciences-nature", "musique", "tech-code"],
            valeurs=["justice-sociale", "creativite", "sens-utilite"],
            onboarding_step1_status=OnboardingStep1Status.IN_PROGRESS,
        )

    def test_completes_step1_and_stamps_timestamp(self, client, user):
        # Pass 1 review M12 — the prior test PATCHed interets against a fresh
        # user with NO passions / NO valeurs and asserted COMPLETED. That
        # behaviour ratified the H3 completion-bypass bug. Fixed: completion
        # now requires the MIN_PASSIONS + MIN_VALEURS prerequisites, so the
        # test must seed them before asserting completion.
        self._seed_passions_and_valeurs(user)
        resp = client.patch(
            URL,
            data={
                "step": "interets",
                "interets": {"1": "Podcast Choses à savoir", "2": "Sapiens", "3": ""},
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        p = StudentProfile.objects.get(user=user)
        assert p.onboarding_step1_status == OnboardingStep1Status.COMPLETED
        assert p.onboarding_step1_completed_at is not None
        # Empty string normalised to None.
        assert p.interets == {"1": "Podcast Choses à savoir", "2": "Sapiens", "3": None}

    def test_accepts_all_null_when_prerequisites_met(self, client, user):
        # An all-null intérêts payload is still a valid completion as long as
        # passions and valeurs have been validated first (AC4 — intérêts
        # entirely optional). Pass 1 M12 fixup — explicitly seed the floors.
        self._seed_passions_and_valeurs(user)
        resp = client.patch(
            URL,
            data={"step": "interets", "interets": {"1": "", "2": "", "3": ""}},
            format="json",
        )
        assert resp.status_code == 200
        p = StudentProfile.objects.get(user=user)
        assert p.interets == {"1": None, "2": None, "3": None}
        assert p.onboarding_step1_status == OnboardingStep1Status.COMPLETED

    def test_interets_without_prerequisites_routes_to_partial_skipped(self, client, user):
        # Pass 1 review H3 — a `step=interets` PATCH against a profile that
        # has not yet met the MIN_PASSIONS / MIN_VALEURS floors must NOT
        # mark the row `completed`. The serializer now downgrades to
        # `partial_skipped` and persists whatever intérêts the user typed,
        # so they don't lose data; the recommendation engine (Epic 3) will
        # later see the row as "step 1 dropped" not "step 1 finished".
        resp = client.patch(
            URL,
            data={
                "step": "interets",
                "interets": {"1": "Podcast Choses à savoir", "2": "", "3": ""},
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        p = StudentProfile.objects.get(user=user)
        assert p.onboarding_step1_status == OnboardingStep1Status.PARTIAL_SKIPPED
        assert p.onboarding_step1_completed_at is None
        # User's typed intérêt is still persisted (UX > strict sync).
        assert p.interets == {"1": "Podcast Choses à savoir", "2": None, "3": None}

    def test_terminal_state_refuses_further_passions_patch(self, client, user):
        # Pass 1 review H2 — once a profile reaches a terminal state
        # (`completed`, `skipped`, `partial_skipped`), further sub-step
        # PATCHes are refused with a typed 400 so a stale tab can't
        # silently overwrite a finished onboarding. `step=skip` is
        # excepted (idempotent reaffirmation).
        StudentProfile.objects.create(
            user=user,
            passions=["sciences-nature", "musique", "tech-code"],
            valeurs=["justice-sociale", "creativite", "sens-utilite"],
            onboarding_step1_status=OnboardingStep1Status.COMPLETED,
        )
        resp = client.patch(
            URL,
            data={"step": "passions", "passions": ["arts-creation", "musique", "sport-corps"]},
            format="json",
        )
        assert resp.status_code == 400
        assert b"terminal state" in resp.content.lower() or b"already" in resp.content.lower()

    def test_rejects_string_over_200_chars(self, client, user):
        self._seed_passions_and_valeurs(user)
        resp = client.patch(
            URL,
            data={"step": "interets", "interets": {"1": "a" * 201, "2": "", "3": ""}},
            format="json",
        )
        assert resp.status_code == 400


# --- PATCH skip (AC7) ------------------------------------------------------


@pytest.mark.django_db
class TestPatchSkip:
    def test_skip_with_no_prior_data_sets_skipped(self, client, user):
        resp = client.patch(URL, data={"step": "skip"}, format="json")
        assert resp.status_code == 200, resp.content
        p = StudentProfile.objects.get(user=user)
        assert p.onboarding_step1_status == OnboardingStep1Status.SKIPPED

    def test_skip_with_prior_data_sets_partial_skipped(self, client, user):
        StudentProfile.objects.create(
            user=user,
            passions=["sciences-nature", "musique", "tech-code"],
            valeurs=["justice-sociale", "creativite", "sens-utilite"],
            onboarding_step1_status=OnboardingStep1Status.IN_PROGRESS,
        )
        resp = client.patch(URL, data={"step": "skip"}, format="json")
        assert resp.status_code == 200, resp.content
        p = StudentProfile.objects.get(user=user)
        assert p.onboarding_step1_status == OnboardingStep1Status.PARTIAL_SKIPPED


# --- Partial PATCH semantics (AC5) ----------------------------------------


@pytest.mark.django_db
class TestPartialPatchSemantics:
    """A PATCH for one sub-step MUST NOT wipe the other sub-steps' fields."""

    def test_patch_passions_keeps_valeurs(self, client, user):
        StudentProfile.objects.create(
            user=user,
            valeurs=["justice-sociale", "creativite", "sens-utilite"],
        )
        client.patch(
            URL,
            data={"step": "passions", "passions": ["sciences-nature", "musique", "tech-code"]},
            format="json",
        )
        p = StudentProfile.objects.get(user=user)
        assert p.passions == ["sciences-nature", "musique", "tech-code"]
        assert p.valeurs == ["justice-sociale", "creativite", "sens-utilite"]

    def test_patch_valeurs_keeps_passions(self, client, user):
        StudentProfile.objects.create(
            user=user,
            passions=["sciences-nature", "musique", "tech-code"],
        )
        client.patch(
            URL,
            data={"step": "valeurs", "valeurs": ["justice-sociale", "creativite", "sens-utilite"]},
            format="json",
        )
        p = StudentProfile.objects.get(user=user)
        assert p.passions == ["sciences-nature", "musique", "tech-code"]
        assert p.valeurs == ["justice-sociale", "creativite", "sens-utilite"]
