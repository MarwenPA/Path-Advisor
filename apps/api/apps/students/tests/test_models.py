"""Model-layer unit tests for `StudentProfile` (Story 2.1 T3).

Run on SQLite (no RLS — the policy is exercised in test_rls.py against PG).
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.students.models import OnboardingStep1Status, StudentProfile

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="sarah@test.local", password="Strong1!password")


@pytest.mark.django_db
class TestStudentProfileDefaults:
    def test_id_is_prefixed_ulid(self, user):
        profile = StudentProfile.objects.create(user=user)
        assert profile.id.startswith("sprf_")
        # `sprf` (4) + `_` (1) + ULID 26 chars = 31 chars total.
        assert len(profile.id) == 31

    def test_passions_defaults_to_empty_list(self, user):
        profile = StudentProfile.objects.create(user=user)
        assert profile.passions == []

    def test_valeurs_defaults_to_empty_list(self, user):
        profile = StudentProfile.objects.create(user=user)
        assert profile.valeurs == []

    def test_interets_defaults_to_three_nulls(self, user):
        profile = StudentProfile.objects.create(user=user)
        assert profile.interets == {"1": None, "2": None, "3": None}

    def test_status_defaults_to_pending(self, user):
        profile = StudentProfile.objects.create(user=user)
        assert profile.onboarding_step1_status == OnboardingStep1Status.PENDING
        assert profile.onboarding_step1_completed_at is None


@pytest.mark.django_db
class TestTenantIdAutoSync:
    """Story 1.8 pattern — tenant_id is denormalized from user.tenant_id."""

    def test_tenant_id_copied_from_user_on_create(self, user):
        import uuid as _uuid

        user.tenant_id = _uuid.uuid4()
        user.save(update_fields=["tenant_id"])

        profile = StudentProfile.objects.create(user=user)
        assert profile.tenant_id == user.tenant_id

    def test_tenant_id_stays_null_for_b2c_user(self, user):
        # Sanity — B2C signup leaves tenant_id null on the user.
        assert user.tenant_id is None
        profile = StudentProfile.objects.create(user=user)
        assert profile.tenant_id is None

    def test_explicit_tenant_id_is_not_overwritten(self, user):
        import uuid as _uuid

        explicit = _uuid.uuid4()
        profile = StudentProfile(user=user, tenant_id=explicit)
        profile.save()
        assert profile.tenant_id == explicit


@pytest.mark.django_db
class TestStatusTransitions:
    def test_mark_completed_sets_timestamp(self, user):
        profile = StudentProfile.objects.create(user=user)
        profile.mark_completed()
        profile.save()
        assert profile.onboarding_step1_status == OnboardingStep1Status.COMPLETED
        assert profile.onboarding_step1_completed_at is not None

    def test_mark_completed_is_idempotent(self, user):
        profile = StudentProfile.objects.create(user=user)
        profile.mark_completed()
        profile.save()
        first_ts = profile.onboarding_step1_completed_at
        profile.mark_completed()
        profile.save()
        assert profile.onboarding_step1_completed_at == first_ts, "timestamp must not move on re-call"

    def test_mark_skipped_partial(self, user):
        profile = StudentProfile.objects.create(user=user)
        profile.mark_skipped(partial=True)
        assert profile.onboarding_step1_status == OnboardingStep1Status.PARTIAL_SKIPPED

    def test_mark_skipped_full(self, user):
        profile = StudentProfile.objects.create(user=user)
        profile.mark_skipped(partial=False)
        assert profile.onboarding_step1_status == OnboardingStep1Status.SKIPPED

    def test_is_step1_completed_property(self, user):
        profile = StudentProfile.objects.create(user=user)
        assert not profile.is_step1_completed
        profile.mark_completed()
        assert profile.is_step1_completed


@pytest.mark.django_db
class TestOneToOneConstraint:
    def test_creating_second_profile_for_same_user_fails(self, user):
        StudentProfile.objects.create(user=user)
        with pytest.raises(Exception):  # noqa: PT011 — IntegrityError on PG, DataError-ish on SQLite
            StudentProfile.objects.create(user=user)

    def test_user_hard_delete_cascades_to_profile(self, user):
        profile = StudentProfile.objects.create(user=user)
        pid = profile.id
        user.delete()
        assert not StudentProfile.objects.filter(id=pid).exists()
