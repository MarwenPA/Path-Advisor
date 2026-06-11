"""`POST /api/v1/profile/access-list/<id>/revoke/` integration tests — Story 1.10 §T7.1."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from allauth.account.models import EmailAddress
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import (
    ParentalConsent,
    ParentalConsentDecision,
    UserRole,
)
from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog
from apps.profiles.access_list.dialog_hashes import CANONICAL_REVOKE_DIALOG_HASHES

# Review D5 — `ParentalConsentSource.revoke` now uses `transaction.on_commit`
# to dispatch the Celery task. The on_commit hook only fires when the
# transaction ACTUALLY commits, which doesn't happen under the default
# pytest-django wrapper (rollback per test). Mark all tests with
# `transaction=True` so commits are real and on_commit callbacks fire.
pytestmark = pytest.mark.django_db(transaction=True)


def _make_student(email: str = "student@example.test"):
    user = UserFactory(email=email, role=UserRole.STUDENT)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


def _granted_consent(student, parent_email: str = "parent@example.test"):
    return ParentalConsent.objects.create(
        student=student,
        parent_email=parent_email,
        token="t-" + parent_email,
        decision=ParentalConsentDecision.GRANTED,
        decided_at=timezone.now(),
    )


def _authed_client(user):
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    return client


_PARENT_HASH = CANONICAL_REVOKE_DIALOG_HASHES["parent"]


def _url(entry_id: str) -> str:
    return f"/api/v1/profile/access-list/{entry_id}/revoke/"


def _body(hash_=_PARENT_HASH) -> dict:
    return {"content_hash": hash_}


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_happy_path_revokes_and_dispatches_notification(mock_task):
    student = _make_student()
    consent = _granted_consent(student)
    client = _authed_client(student)
    entry_id = f"parental_consent:{consent.id}"

    response = client.post(_url(entry_id), data=_body(), format="json")

    assert response.status_code == 200
    assert response.json() == {"revoked": True, "id": entry_id}

    consent.refresh_from_db()
    assert consent.revoked_at is not None
    mock_task.delay.assert_called_once_with(str(consent.id))


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_revoked_entry_does_not_appear_in_subsequent_get(mock_task):
    student = _make_student()
    consent = _granted_consent(student)
    client = _authed_client(student)
    entry_id = f"parental_consent:{consent.id}"

    client.post(_url(entry_id), data=_body(), format="json")
    list_response = client.get("/api/v1/profile/access-list/")
    assert list_response.json()["results"] == []
    mock_task.delay.assert_called_once()


def test_404_when_entry_id_belongs_to_another_student():
    student_a = _make_student(email="a@example.test")
    student_b = _make_student(email="b@example.test")
    consent_b = _granted_consent(student_b, parent_email="b-parent@example.test")
    client = _authed_client(student_a)
    entry_id = f"parental_consent:{consent_b.id}"

    response = client.post(_url(entry_id), data=_body(), format="json")
    assert response.status_code == 404
    rows = AuditLog.objects.filter(action="profile.access_revoke_attempted").order_by("-created_at")
    # Review P9 — reason is "not_found" (we deliberately collapse "row absent"
    # and "ownership mismatch" into the same audit reason from the student's
    # POV so the endpoint cannot be used as an oracle to probe other students'
    # grant ids).
    assert rows.first().metadata["reason"] == "not_found"
    # Most importantly : student B's consent was NOT touched
    consent_b.refresh_from_db()
    assert consent_b.revoked_at is None


def test_404_when_id_format_is_malformed():
    student = _make_student()
    client = _authed_client(student)

    response = client.post(_url("not-a-composite-id"), data=_body(), format="json")
    assert response.status_code == 404


def test_404_when_source_name_is_unknown():
    student = _make_student()
    client = _authed_client(student)

    response = client.post(_url("bogus:abc"), data=_body(), format="json")
    assert response.status_code == 404
    rows = AuditLog.objects.filter(action="profile.access_revoke_attempted").order_by("-created_at")
    assert rows.first().metadata["reason"] == "unknown_source"


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_content_hash_is_stored_in_audit_metadata(mock_task):
    """Story 1.14 pattern : the hash proves what the user saw, stored on the
    audit row for forensic traceability (NOT used as a gate)."""
    student = _make_student()
    consent = _granted_consent(student)
    client = _authed_client(student)
    entry_id = f"parental_consent:{consent.id}"

    arbitrary_hash = "deadbeef" * 8  # 64 chars
    response = client.post(_url(entry_id), data={"content_hash": arbitrary_hash}, format="json")
    assert response.status_code == 200
    rows = AuditLog.objects.filter(action="profile.access_revoked").order_by("-created_at")
    assert rows.first().metadata["content_hash"] == arbitrary_hash
    mock_task.delay.assert_called_once()


def test_403_for_non_student_roles():
    for role in (
        UserRole.PARENT,
        UserRole.COUNSELOR,
        UserRole.SCHOOL_ADMIN,
        UserRole.PATH_ADMIN,
        UserRole.SUPPORT,
    ):
        user = UserFactory(email=f"{role.value}-rev@example.test", role=role)
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        client = _authed_client(user)
        response = client.post(_url("parental_consent:x"), data=_body(), format="json")
        assert response.status_code == 403, f"Role {role.value} → {response.status_code}"


def test_401_for_anonymous():
    """Review P14 — lock the contract. DRF returns 401 (not 403) for
    `IsAuthenticated` denial when no auth credentials are supplied (the
    standard WWW-Authenticate-bearing response)."""
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    response = client.post(_url("parental_consent:x"), data=_body(), format="json")
    assert response.status_code == 401


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_idempotent_on_double_revoke_writes_exactly_one_audit_row(mock_task):
    """Story 1.10 §AC9 (review P4) — second POST on already-revoked row →
    200 + EXACTLY ONE task dispatch + EXACTLY ONE `profile.access_revoked`
    audit row. The revoker skips the second audit because the source returns
    `RevocationResult.ALREADY_REVOKED`.
    """
    student = _make_student()
    consent = _granted_consent(student)
    client = _authed_client(student)
    entry_id = f"parental_consent:{consent.id}"

    # First revoke
    response_1 = client.post(_url(entry_id), data=_body(), format="json")
    assert response_1.status_code == 200
    audit_count_after_first = AuditLog.objects.filter(action="profile.access_revoked").count()

    # Second revoke
    response_2 = client.post(_url(entry_id), data=_body(), format="json")
    assert response_2.status_code == 200
    assert response_2.json().get("already_revoked") is True
    audit_count_after_second = AuditLog.objects.filter(action="profile.access_revoked").count()

    # §AC9 strict — exactly ONE audit row + exactly ONE Celery dispatch.
    assert audit_count_after_second == audit_count_after_first, (
        "Story 1.10 §AC9 strict: only ONE `profile.access_revoked` row per logical revocation"
    )
    mock_task.delay.assert_called_once()


# ---------------------------------------------------------------------------
# Review P3 — revoke filter rejects pending / refused consents
# ---------------------------------------------------------------------------


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_404_when_revoking_a_pending_consent(mock_task):
    """Review P3 — pending consent (decision=NULL) MUST NOT be revocable.
    Otherwise, a crafted POST stamps `revoked_at` + spam-emails the parent."""
    student = _make_student()
    consent = ParentalConsent.objects.create(
        student=student,
        parent_email="pending@example.test",
        token="t-pending",
        # No decision yet
    )
    client = _authed_client(student)
    response = client.post(_url(f"parental_consent:{consent.id}"), data=_body(), format="json")
    assert response.status_code == 404
    consent.refresh_from_db()
    assert consent.revoked_at is None
    mock_task.delay.assert_not_called()


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_404_when_revoking_a_refused_consent(mock_task):
    """Review P3 — refused consent MUST NOT be revocable."""
    student = _make_student()
    consent = ParentalConsent.objects.create(
        student=student,
        parent_email="refused@example.test",
        token="t-refused",
        decision=ParentalConsentDecision.REFUSED,
        decided_at=timezone.now(),
    )
    client = _authed_client(student)
    response = client.post(_url(f"parental_consent:{consent.id}"), data=_body(), format="json")
    assert response.status_code == 404
    consent.refresh_from_db()
    assert consent.revoked_at is None
    mock_task.delay.assert_not_called()


# ---------------------------------------------------------------------------
# Review P15 — entry_id format validation
# ---------------------------------------------------------------------------


def test_404_on_malformed_entry_id_with_newline():
    """Review P15 — entry_id with embedded newlines (log-injection attempt)
    MUST 404 before any DB lookup or audit subject_id write."""
    student = _make_student()
    client = _authed_client(student)
    response = client.post(_url("parental_consent:abc%0Aevil"), data=_body(), format="json")
    # Django decodes %0A → \n in the URL path ; our regex rejects it.
    assert response.status_code == 404


def test_404_on_entry_id_without_colon():
    student = _make_student()
    client = _authed_client(student)
    response = client.post(_url("no-colon-here"), data=_body(), format="json")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Review P12 — content_hash format validation
# ---------------------------------------------------------------------------


def test_400_when_content_hash_is_not_a_hex_string():
    student = _make_student()
    consent = _granted_consent(student)
    client = _authed_client(student)
    response = client.post(
        _url(f"parental_consent:{consent.id}"),
        data={"content_hash": "not-hex!"},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["type"].endswith("/content-hash-invalid")


def test_400_when_content_hash_is_non_string():
    student = _make_student()
    consent = _granted_consent(student)
    client = _authed_client(student)
    response = client.post(
        _url(f"parental_consent:{consent.id}"),
        data={"content_hash": 12345},
        format="json",
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Review P10 — audit metadata enrichment (tier_type + display_name)
# ---------------------------------------------------------------------------


@patch("apps.accounts.tasks.notify_parental_consent_revoked")
def test_audit_metadata_includes_tier_type_and_display_name(mock_task):
    """Review P10 — Story 1.10 §AC5 mandates self-contained audit metadata."""
    student = _make_student()
    consent = _granted_consent(student, parent_email="metadata-test@example.test")
    client = _authed_client(student)
    response = client.post(_url(f"parental_consent:{consent.id}"), data=_body(), format="json")
    assert response.status_code == 200
    row = AuditLog.objects.filter(action="profile.access_revoked").order_by("-created_at").first()
    assert row.metadata["tier_type"] == "parent"
    assert row.metadata["display_name"] == "metadata-test@example.test"
