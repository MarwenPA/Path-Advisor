"""Story 10.4 — RDV visio : création à l'acceptation, lien, rappels beat.

Contrats : accepter un créneau matérialise un `InterviewMeeting` typé avec
un lien visio non devinable ; l'élève reçoit la confirmation (moteur 8.2 +
push) et l'école reçoit date + lien ; le beat J-1/H-1 se réclame par UPDATE
conditionnel (jamais deux fois, jamais après le début) ; un slot legacy
illisible n'empêche pas l'acceptation.
"""

from __future__ import annotations

from datetime import timedelta
from unittest import mock

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachRequestStatus,
    EarlyOutreachResponse,
    EarlyOutreachResponseAction,
    InterviewMeeting,
)
from apps.outreach.tasks import send_interview_reminders
from apps.professions.models import Profession
from apps.schools.models import School, SchoolStaff

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_meeting_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


@pytest.fixture
def student() -> User:
    return _uf(email="eleve-visio@test.local", role=UserRole.STUDENT)


@pytest.fixture
def school(db) -> School:
    return School.objects.create(
        slug="ecole-visio-test",
        name="École Visio Test",
        type=School.Type.ECOLE_INGENIEUR,
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
        postal_code="69000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
    )


@pytest.fixture
def profession(db) -> Profession:
    return Profession.objects.create(
        slug="metier-visio-test",
        name="Métier Visio Test",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )


@pytest.fixture
def school_admin(school) -> User:
    user = _uf(email="admin-ecole-visio@test.local", role=UserRole.SCHOOL_ADMIN)
    with bypass_rls(reason="test_setup.link_school_staff"):
        SchoolStaff.objects.create(user=user, school=school)
    return user


def _outreach_with_interview(student, school, profession, slots=None) -> EarlyOutreachRequest:
    with bypass_rls(reason="test_setup.create_outreach_interview"):
        outreach = EarlyOutreachRequest.objects.create(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.RESPONDED,
        )
        EarlyOutreachResponse.objects.create(
            request=outreach,
            action=EarlyOutreachResponseAction.INTERVIEW_REQUESTED,
            proposed_slots=slots or ["2026-10-01T10:00:00Z", "2026-10-02T14:00:00Z"],
        )
    return outreach


def _accept(student, outreach, slot, capture):
    client = APIClient()
    client.force_authenticate(user=student)
    with capture(execute=True):
        response = client.post(
            f"/api/v1/outreach/requests/{outreach.id}/interview/accept/",
            {"slot": slot},
            format="json",
        )
    return response


# ─── Création du RDV à l'acceptation ─────────────────────────────────────────


def test_accept_creates_typed_meeting_with_visio_link(
    student, school, profession, school_admin, django_capture_on_commit_callbacks, settings
):
    settings.VISIO_BASE_URL = "https://visio.path-advisor.fr"
    outreach = _outreach_with_interview(student, school, profession)

    r = _accept(student, outreach, "2026-10-01T10:00:00Z", django_capture_on_commit_callbacks)
    assert r.status_code == 200, r.content

    meeting = InterviewMeeting.objects.get(outreach=outreach)
    assert meeting.scheduled_at.isoformat() == "2026-10-01T10:00:00+00:00"
    assert meeting.visio_url.startswith("https://visio.path-advisor.fr/path-advisor-")
    assert len(meeting.room_slug) > 20  # non devinable

    # Élève : confirmation avec lien ; école : date + lien.
    bodies = {m.to[0]: m.body for m in mail.outbox}
    assert meeting.visio_url in bodies["eleve-visio@test.local"]
    assert "enregistrée" in bodies["eleve-visio@test.local"]  # AC3 dans la copie
    assert meeting.visio_url in bodies["admin-ecole-visio@test.local"]


def test_accept_enqueues_push_confirmation(
    student, school, profession, school_admin, django_capture_on_commit_callbacks
):
    outreach = _outreach_with_interview(student, school, profession)
    with mock.patch("apps.notifications.tasks.send_web_push.delay") as delay:
        r = _accept(student, outreach, "2026-10-01T10:00:00Z", django_capture_on_commit_callbacks)
    assert r.status_code == 200
    assert delay.called
    args = delay.call_args.args
    assert args[0] == student.id and args[2]["title"] == "Entretien confirmé"
    assert school.name not in args[2]["body"]  # écran verrouillé : jamais le nom


def test_unparseable_legacy_slot_still_accepts_without_meeting(
    student, school, profession, school_admin, django_capture_on_commit_callbacks
):
    outreach = _outreach_with_interview(
        student, school, profession, slots=["mardi prochain", "2026-10-02T14:00:00Z"]
    )
    r = _accept(student, outreach, "mardi prochain", django_capture_on_commit_callbacks)
    assert r.status_code == 200
    assert not InterviewMeeting.objects.filter(outreach=outreach).exists()


def test_meeting_exposed_in_student_serializer(
    student, school, profession, school_admin, django_capture_on_commit_callbacks
):
    outreach = _outreach_with_interview(student, school, profession)
    _accept(student, outreach, "2026-10-01T10:00:00Z", django_capture_on_commit_callbacks)

    client = APIClient()
    client.force_authenticate(user=student)
    body = client.get("/api/v1/outreach/requests/").json()
    row = next(r for r in body["results"] if r["id"] == outreach.id)
    assert row["response"]["meeting"]["visio_url"].endswith(
        InterviewMeeting.objects.get(outreach=outreach).room_slug
    )
    assert row["response"]["meeting"]["scheduled_at"].startswith("2026-10-01T10:00")


# ─── Beat de rappels ─────────────────────────────────────────────────────────


def _meeting(student, school, profession, *, in_hours: float) -> InterviewMeeting:
    outreach = _outreach_with_interview(student, school, profession)
    with bypass_rls(reason="test_setup.create_meeting"):
        return InterviewMeeting.objects.create(
            outreach=outreach,
            scheduled_at=timezone.now() + timedelta(hours=in_hours),
        )


def test_reminder_24h_sent_once(student, school, profession, django_capture_on_commit_callbacks):
    meeting = _meeting(student, school, profession, in_hours=20)

    with django_capture_on_commit_callbacks(execute=True):
        first = send_interview_reminders()
    assert first == {"24h": 1, "1h": 0}
    assert any("demain" in m.subject for m in mail.outbox)

    meeting.refresh_from_db()
    assert meeting.reminder_24h_sent_at is not None

    second = send_interview_reminders()
    assert second == {"24h": 0, "1h": 0}  # claim : jamais deux fois


def test_reminder_1h_window(student, school, profession, django_capture_on_commit_callbacks):
    _meeting(student, school, profession, in_hours=0.5)
    with django_capture_on_commit_callbacks(execute=True):
        sent = send_interview_reminders()
    # À 30 min de l'entretien, les DEUX fenêtres sont dues — J-1 n'était
    # jamais passé (RDV pris en dernière minute) : on envoie les deux.
    assert sent == {"24h": 1, "1h": 1}
    assert any("commence dans une heure" in m.subject for m in mail.outbox)


def test_no_reminder_after_meeting_started(student, school, profession):
    _meeting(student, school, profession, in_hours=-1)
    assert send_interview_reminders() == {"24h": 0, "1h": 0}
