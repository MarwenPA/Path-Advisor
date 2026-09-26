"""Story 9.4 — back-office moderation (motivations + commentaires écoles).

Contracts: queue oldest-first with business-hours SLA + prescreen AID;
approve reuses the 5.5 unblock semantics; reject demands the typed
category AND a reason; a school comment is gated a-priori — the response
email leaves WITHOUT it, /mes-envois hides it until approval, a rejected
one never surfaces; every decision is audited.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.audit.tests.factories import PathAdminUserFactory
from apps.core.rls_testing import as_path_admin
from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachRequestStatus,
    EarlyOutreachResponse,
)
from apps.outreach.services.prescreen import prescreen_text
from apps.outreach.services.school_response import respond_to_outreach_request
from apps.professions.models import Profession
from apps.schools.models import School

MOTIVATIONS_URL = "/api/v1/admin/moderation/motivations/"
COMMENTS_URL = "/api/v1/admin/moderation/school-comments/"


@pytest.fixture
def admin(db):
    return PathAdminUserFactory(email="karim-94@test.local", email_verified_at=timezone.now())


@pytest.fixture
def client(admin) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


def _mk_outreach(email: str, *, motivation: str = "", status=None) -> EarlyOutreachRequest:
    with as_path_admin():
        student = User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    school, _ = School.objects.get_or_create(
        slug="ecole-mod-94",
        defaults=dict(
            name="École Mod 9.4",
            type=School.Type.ECOLE_INGENIEUR,
            city="Lyon",
            region="ARA",
            postal_code="69000",
            selectivity_index=2,
            public_private=School.PublicPrivate.PUBLIC,
            description="x" * 20,
            official_url="https://test.example",
        ),
    )
    profession, _ = Profession.objects.get_or_create(
        slug="metier-mod-94",
        defaults=dict(
            name="Métier Mod",
            description="x" * 120,
            daily_routine="x" * 90,
            prospects_text="a. b. c.",
            is_active=True,
        ),
    )
    with as_path_admin():
        return EarlyOutreachRequest.objects.create(
            student=student,
            school=school,
            profession=profession,
            motivation_text=motivation,
            status=status or EarlyOutreachRequestStatus.PENDING_MODERATION,
        )


# ---------------------------------------------------------------------------
# Prescreen (pure)
# ---------------------------------------------------------------------------


def test_prescreen_flags_pii_and_risk_words():
    result = prescreen_text(
        "Contactez ma mère au 06 12 34 56 78 ou mere@example.fr — sinon je vais tout niquer."
    )
    assert set(result["pii"]) == {"email", "telephone"}
    assert result["risk"]  # the slur family matched
    assert prescreen_text("Je suis motivé par la robotique depuis la 4e.") == {
        "pii": [],
        "risk": [],
    }


# ---------------------------------------------------------------------------
# Motivations queue
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_queue_carries_sla_and_prescreen(client):
    fresh = _mk_outreach("frais-94@test.local", motivation="Je rêve de ce métier.")
    stale = _mk_outreach("vieux-94@test.local", motivation="Appelle-moi au 06 11 22 33 44.")
    # Age the stale one past 24 business hours (2 full weekdays back,
    # anchored mid-week safe via 4 days).
    EarlyOutreachRequest.objects.filter(pk=stale.pk).update(
        created_at=timezone.now() - timedelta(days=4)
    )

    data = client.get(MOTIVATIONS_URL).json()
    ids = [row["id"] for row in data["results"]]
    assert ids == [stale.pk, fresh.pk]  # oldest first
    by_id = {row["id"]: row for row in data["results"]}
    assert by_id[stale.pk]["overdue"] is True
    assert by_id[fresh.pk]["overdue"] is False
    assert data["overdue_count"] == 1
    assert by_id[stale.pk]["prescreen"]["pii"] == ["telephone"]  # the AID


@pytest.mark.django_db(transaction=True)
def test_approve_unblocks_via_the_55_semantics(client, django_capture_on_commit_callbacks):
    outreach = _mk_outreach("approuve-94@test.local", motivation="Motivation sérieuse.")

    with django_capture_on_commit_callbacks(execute=True):
        resp = client.post(f"{MOTIVATIONS_URL}{outreach.pk}/approve/")
    assert resp.status_code == 200

    outreach.refresh_from_db()
    assert outreach.status == EarlyOutreachRequestStatus.PENDING  # unblocked, sendable
    assert AuditLog.objects.filter(action="moderation.motivation_approved").exists()
    assert len(mail.outbox) >= 1  # the 5.5 student email rode along


@pytest.mark.django_db(transaction=True)
def test_reject_requires_typed_category_and_reason(client, django_capture_on_commit_callbacks):
    outreach = _mk_outreach("rejet-94@test.local", motivation="Texte problématique.")

    assert (
        client.post(f"{MOTIVATIONS_URL}{outreach.pk}/reject/", {"reason": "x"}).status_code == 400
    )
    assert (
        client.post(
            f"{MOTIVATIONS_URL}{outreach.pk}/reject/", {"category": "discrimination"}
        ).status_code
        == 400
    )
    outreach.refresh_from_db()
    assert outreach.status == EarlyOutreachRequestStatus.PENDING_MODERATION  # untouched

    with django_capture_on_commit_callbacks(execute=True):
        resp = client.post(
            f"{MOTIVATIONS_URL}{outreach.pk}/reject/",
            {"category": "donnees_tierces", "reason": "Le texte contient le téléphone d'un tiers."},
        )
    assert resp.status_code == 200
    outreach.refresh_from_db()
    assert outreach.status == EarlyOutreachRequestStatus.REJECTED
    assert outreach.rejection_category == "donnees_tierces"
    assert AuditLog.objects.filter(action="moderation.motivation_rejected").exists()

    # State guard: acting twice → 409.
    assert client.post(f"{MOTIVATIONS_URL}{outreach.pk}/approve/").status_code == 409


@pytest.mark.django_db
def test_moderation_refuses_non_admin(db):
    with as_path_admin():
        student = User.objects.create_user(
            email="intrus-94@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    c = APIClient()
    c.force_authenticate(user=student)
    assert c.get(MOTIVATIONS_URL).status_code == 403
    assert c.get(COMMENTS_URL).status_code == 403


# ---------------------------------------------------------------------------
# School comments (amendement P2-5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_school_comment_is_gated_until_approved(client, django_capture_on_commit_callbacks):
    outreach = _mk_outreach("gate-94@test.local", status=EarlyOutreachRequestStatus.PENDING)

    with django_capture_on_commit_callbacks(execute=True):
        respond_to_outreach_request(
            outreach=outreach,
            action="interested",
            comment="Très bon dossier — appelle-nous au 04 78 00 00 00.",
        )

    response = EarlyOutreachResponse.objects.get(request=outreach)
    assert response.comment_status == EarlyOutreachResponse.CommentStatus.PENDING

    # 1. The response email LEFT immediately — WITHOUT the comment.
    assert len(mail.outbox) == 1
    assert "appelle-nous" not in mail.outbox[0].body

    # 2. In-app, the comment is hidden while pending (flag exposed instead).
    from apps.outreach.serializers import EarlyOutreachResponseSerializer

    data = EarlyOutreachResponseSerializer(response).data
    assert data["comment"] == ""
    assert data["comment_pending"] is True

    # 3. The moderation queue sees it, with the prescreen AID.
    queue = client.get(COMMENTS_URL).json()
    row = next(r for r in queue["results"] if r["id"] == response.pk)
    assert row["prescreen"]["pii"] == ["telephone"]

    # 4. Approve → visible in-app.
    assert client.post(f"{COMMENTS_URL}{response.pk}/approve/").status_code == 200
    response.refresh_from_db()
    data = EarlyOutreachResponseSerializer(response).data
    assert "appelle-nous" in data["comment"]
    assert data["comment_pending"] is False
    assert AuditLog.objects.filter(action="moderation.school_comment_approved").exists()


@pytest.mark.django_db(transaction=True)
def test_rejected_school_comment_never_reaches_the_student(
    client, django_capture_on_commit_callbacks
):
    outreach = _mk_outreach("rejetc-94@test.local", status=EarlyOutreachRequestStatus.PENDING)
    with django_capture_on_commit_callbacks(execute=True):
        respond_to_outreach_request(
            outreach=outreach, action="not_aligned", comment="Commentaire déplacé."
        )
    response = EarlyOutreachResponse.objects.get(request=outreach)

    assert client.post(f"{COMMENTS_URL}{response.pk}/reject/").status_code == 200
    response.refresh_from_db()
    assert response.comment_status == EarlyOutreachResponse.CommentStatus.REJECTED

    from apps.outreach.serializers import EarlyOutreachResponseSerializer

    data = EarlyOutreachResponseSerializer(response).data
    assert data["comment"] == ""
    assert data["comment_pending"] is False  # terminal — no false hope
    # Acting twice → 409.
    assert client.post(f"{COMMENTS_URL}{response.pk}/approve/").status_code == 409


@pytest.mark.django_db(transaction=True)
def test_empty_comment_needs_no_moderation(client, django_capture_on_commit_callbacks):
    outreach = _mk_outreach("vide-94@test.local", status=EarlyOutreachRequestStatus.PENDING)
    with django_capture_on_commit_callbacks(execute=True):
        respond_to_outreach_request(outreach=outreach, action="interested")
    response = EarlyOutreachResponse.objects.get(request=outreach)
    assert response.comment_status == EarlyOutreachResponse.CommentStatus.APPROVED
    assert client.get(COMMENTS_URL).json()["results"] == []  # nothing to review
