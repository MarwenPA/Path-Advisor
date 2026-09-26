"""Revue Epic 8 — pins for the notifications fixes (lots A, B, C, E).

Each test names the finding it locks in.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.notifications.delta_recap import compute_cards
from apps.notifications.models import (
    DeltaRecapCursor,
    MilestoneKind,
    NewSchoolsDigestRun,
    NotificationCategory,
    NotificationPreference,
    ParcoursupMilestone,
)
from apps.notifications.tasks import (
    send_new_schools_digest,
    send_parcoursup_milestone_notifications,
)
from apps.professions.models import Profession
from apps.schools.models import Parcours, School
from apps.students.models import StudentLevelProfile, StudentProfile

RECAP_URL = "/api/v1/me/delta-recap/"
ACK_URL = "/api/v1/me/delta-recap/ack/"

MATCHING_SIGNALS = {
    "passions": ["sciences", "robotique"],
    "valeurs": ["autonomie"],
    "specialites": [],
}


def _mk_student(email: str, *, level: str = "lycee_terminale", role=UserRole.STUDENT) -> User:
    with as_path_admin():
        user = User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=role,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        if role == UserRole.STUDENT:
            profile = StudentProfile.objects.create(
                user=user, passions=["sciences"], valeurs=["autonomie"]
            )
            StudentLevelProfile.objects.create(profile=profile, level=level)
    return user


def _mk_school(slug: str, *, profession_name: str | None = None, signals=None) -> School:
    school = School.objects.create(
        slug=slug,
        name=f"École {slug}",
        type=School.Type.ECOLE_INGENIEUR,
        city="Lyon",
        region="ARA",
        postal_code="69000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
        is_active=True,
    )
    if profession_name is not None:
        profession = Profession.objects.create(
            slug=f"metier-{slug}",
            name=profession_name,
            description="x" * 20,
            daily_routine="x" * 20,
            prospects_text="x",
            is_active=True,
            signals_json=signals or MATCHING_SIGNALS,
        )
        Parcours.objects.create(
            profession=profession,
            target_school=school,
            niveau_scolaire="terminale_generale",
            label="Voie",
        )
    return school


def _age_cursor(user, *, days: int) -> None:
    DeltaRecapCursor.objects.update_or_create(
        user=user, defaults={"seen_at": timezone.now() - timedelta(days=days)}
    )


# ---------------------------------------------------------------------------
# P0-1 — milestone atomic claim
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_milestone_claim_is_conditional(django_capture_on_commit_callbacks):
    """The claim primitive: once `notified_at` is set — even a microsecond
    earlier by a concurrent run — the conditional UPDATE matches 0 rows and
    the run sends NOTHING for that milestone."""
    _mk_student("claim@test.local")
    milestone = ParcoursupMilestone.objects.create(
        kind=MilestoneKind.OUVERTURE,
        campaign="claim-test",
        date=timezone.localdate() + timedelta(days=5),
        notify_days_before=10,
    )
    # Simulate the concurrent run winning the claim between the due-list
    # read and this run's claim.
    ParcoursupMilestone.objects.filter(pk=milestone.pk).update(notified_at=timezone.now())

    with django_capture_on_commit_callbacks(execute=True):
        queued = send_parcoursup_milestone_notifications()

    assert queued == 0
    assert len(mail.outbox) == 0


@pytest.mark.django_db(transaction=True)
def test_milestone_sends_exactly_once_across_two_runs(django_capture_on_commit_callbacks):
    _mk_student("once@test.local")
    ParcoursupMilestone.objects.create(
        kind=MilestoneKind.OUVERTURE,
        campaign="once-test",
        date=timezone.localdate() + timedelta(days=5),
        notify_days_before=10,
    )
    with django_capture_on_commit_callbacks(execute=True):
        assert send_parcoursup_milestone_notifications() == 1
        assert send_parcoursup_milestone_notifications() == 0
    assert len(mail.outbox) == 1


# ---------------------------------------------------------------------------
# P1-5 — past-date milestones are never announced in the present tense
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_past_milestone_is_marked_missed_not_sent(django_capture_on_commit_callbacks):
    _mk_student("missed@test.local")
    stale = ParcoursupMilestone.objects.create(
        kind=MilestoneKind.OUVERTURE,
        campaign="missed-test",
        date=timezone.localdate() - timedelta(days=3),
        notify_days_before=10,
    )

    with django_capture_on_commit_callbacks(execute=True):
        assert send_parcoursup_milestone_notifications() == 0

    assert len(mail.outbox) == 0
    stale.refresh_from_db()
    assert stale.notified_at is not None  # consumed, never re-candidate


# ---------------------------------------------------------------------------
# P2-2 — digest window anchored on the last run (contiguous by construction)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_digest_window_anchors_on_last_run(django_capture_on_commit_callbacks):
    """A school created 10 days ago — OUTSIDE now()-7d — must still be
    digested when the previous run predates it (the old anchoring silently
    skipped it forever)."""
    _mk_student("anchor@test.local")
    school = _mk_school("ecole-anchor", profession_name="Métier Anchor")
    School.objects.filter(pk=school.pk).update(created_at=timezone.now() - timedelta(days=10))
    run = NewSchoolsDigestRun.objects.create(week="2026-W37", emails_queued=0)
    NewSchoolsDigestRun.objects.filter(pk=run.pk).update(
        sent_at=timezone.now() - timedelta(days=12)
    )

    with django_capture_on_commit_callbacks(execute=True):
        assert send_new_schools_digest() == 1
    assert len(mail.outbox) == 1


# ---------------------------------------------------------------------------
# P3 — digest subject names a profession only when it is unique
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_digest_subject_drops_profession_when_ambiguous(django_capture_on_commit_callbacks):
    _mk_student("ambigu@test.local")
    _mk_school("ecole-a", profession_name="Ingénierie biomédicale")
    _mk_school("ecole-b", profession_name="Robotique industrielle")

    with django_capture_on_commit_callbacks(execute=True):
        assert send_new_schools_digest() == 1

    subject = mail.outbox[0].subject
    assert subject == "2 nouvelles écoles correspondent à ton profil"
    assert "Ingénierie" not in subject and "Robotique" not in subject


@pytest.mark.django_db(transaction=True)
def test_digest_subject_keeps_a_unique_profession(django_capture_on_commit_callbacks):
    _mk_student("unique@test.local")
    _mk_school("ecole-u", profession_name="Ingénierie biomédicale")

    with django_capture_on_commit_callbacks(execute=True):
        assert send_new_schools_digest() == 1
    assert mail.outbox[0].subject == (
        "1 nouvelle école correspond à ton profil Ingénierie biomédicale"
    )


# ---------------------------------------------------------------------------
# P1-3 — calendar card audience parity with the 8.3 emails
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_calendar_card_never_shown_to_a_seconde():
    seconde = _mk_student("seconde@test.local", level="lycee_seconde")
    terminale = _mk_student("terminale@test.local", level="lycee_terminale")
    ParcoursupMilestone.objects.create(
        kind=MilestoneKind.OUVERTURE,
        campaign="audience-test",
        date=timezone.localdate() + timedelta(days=5),
        notify_days_before=30,
    )
    since = timezone.now() - timedelta(days=30)

    kinds_seconde = {c["kind"] for c in compute_cards(seconde, since)}
    kinds_terminale = {c["kind"] for c in compute_cards(terminale, since)}
    assert "parcoursup_milestone" not in kinds_seconde
    assert "parcoursup_milestone" in kinds_terminale


# ---------------------------------------------------------------------------
# P1-4 — same-date milestones: pick the one IN ITS WINDOW, not `.first()`
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_calendar_card_survives_same_date_milestones():
    """The REAL seed shape: J-30-fermeture (window 30 d) and fermeture
    (window 7 d) on the same date. At J-18 only the first is in window —
    the card must exist whatever the DB row order."""
    student = _mk_student("samedate@test.local")
    target = timezone.localdate() + timedelta(days=18)
    # Create the narrow-window one FIRST so a naive `.first()` tie-break by
    # insertion order would pick it and blank the card.
    ParcoursupMilestone.objects.create(
        kind=MilestoneKind.FERMETURE_VOEUX,
        campaign="samedate-test",
        date=target,
        notify_days_before=7,
    )
    ParcoursupMilestone.objects.create(
        kind=MilestoneKind.J30_FERMETURE_VOEUX,
        campaign="samedate-test",
        date=target,
        notify_days_before=30,
    )

    cards = compute_cards(student, timezone.now() - timedelta(days=30))
    card = next(c for c in cards if c["kind"] == "parcoursup_milestone")
    assert card["days_until"] == 18
    assert "fermeture des vœux approche" in card["title"]  # the J-30 copy


# ---------------------------------------------------------------------------
# P2-1 — stat chip: temporal filter + no promise without a stat
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_stale_stat_is_not_attributed_to_a_fresh_response():
    from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachResponse
    from apps.schools.models import AdmissionStat

    student = _mk_student("stalestat@test.local")
    school = _mk_school("ecole-stale")
    profession = Profession.objects.create(
        slug="metier-stale",
        name="Métier Stale",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )
    with as_path_admin():
        request = EarlyOutreachRequest.objects.create(
            student=student, school=school, profession=profession
        )
        EarlyOutreachResponse.objects.create(request=request, action="interested")
        # A stat whose delta PREDATES the cursor window (old response or a
        # bulletin re-upload) — previously shown as this response's delta.
        AdmissionStat.objects.create(
            school=school,
            user=student,
            min_proba=30,
            expected_proba=55,
            max_proba=70,
            previous_proba=45,
            label=AdmissionStat.Label.REALISTE,
            outreach_delta_applied_at=timezone.now() - timedelta(days=60),
        )

    since = timezone.now() - timedelta(days=30)
    card = next(c for c in compute_cards(student, since) if c["kind"] == "school_response")
    assert card["stat_before"] is None and card["stat_after"] is None
    # And the body never PROMISES an update it cannot show (P2-1b).
    assert "mise à jour" not in card["body"]


@pytest.mark.django_db
def test_body_mentions_the_stat_only_when_it_rides_along():
    from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachResponse
    from apps.schools.models import AdmissionStat

    student = _mk_student("freshstat@test.local")
    school = _mk_school("ecole-fresh")
    profession = Profession.objects.create(
        slug="metier-fresh",
        name="Métier Fresh",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )
    with as_path_admin():
        request = EarlyOutreachRequest.objects.create(
            student=student, school=school, profession=profession
        )
        EarlyOutreachResponse.objects.create(request=request, action="interested")
        AdmissionStat.objects.create(
            school=school,
            user=student,
            min_proba=30,
            expected_proba=55,
            max_proba=70,
            previous_proba=45,
            label=AdmissionStat.Label.REALISTE,
            outreach_delta_applied_at=timezone.now(),
        )

    since = timezone.now() - timedelta(days=30)
    card = next(c for c in compute_cards(student, since) if c["kind"] == "school_response")
    assert card["stat_before"] == 45 and card["stat_after"] == 55
    assert "mise à jour" in card["body"]


# ---------------------------------------------------------------------------
# P3 — recap bounds
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_response_cards_are_capped():
    from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachResponse

    student = _mk_student("caps@test.local")
    with as_path_admin():
        for i in range(7):
            school = _mk_school(f"ecole-cap-{i}")
            profession = Profession.objects.create(
                slug=f"metier-cap-{i}",
                name=f"Métier Cap {i}",
                description="x" * 20,
                daily_routine="x" * 20,
                prospects_text="x",
                is_active=True,
            )
            request = EarlyOutreachRequest.objects.create(
                student=student, school=school, profession=profession
            )
            EarlyOutreachResponse.objects.create(request=request, action="interested")

    since = timezone.now() - timedelta(days=30)
    cards = [c for c in compute_cards(student, since) if c["kind"] == "school_response"]
    assert len(cards) == 5  # RECAP_MAX_RESPONSE_CARDS — the rest lives in /mes-envois


# ---------------------------------------------------------------------------
# P2-9 / P3 — the recap API is student-only and state-free for other roles
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_non_student_gets_empty_recap_and_no_cursor():
    parent = _mk_student("parent-recap@test.local", role=UserRole.PARENT)
    client = APIClient()
    client.force_authenticate(user=parent)

    resp = client.get(RECAP_URL)
    assert resp.status_code == 200
    assert resp.json() == {"cards": []}
    # The GET used to CREATE a cursor for a parent who followed /accueil.
    assert not DeltaRecapCursor.objects.filter(user=parent).exists()

    assert client.post(ACK_URL).status_code == 204
    assert not DeltaRecapCursor.objects.filter(user=parent).exists()


# ---------------------------------------------------------------------------
# P2-7 — unsubscribe click from a deleted account: idempotent, never a 500
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unsubscribe_token_of_deleted_account_is_graceful():
    from apps.notifications.tokens import make_unsubscribe_token

    student = _mk_student("deleted-unsub@test.local")
    token = make_unsubscribe_token(student.id, NotificationCategory.NEW_SCHOOLS)
    with as_path_admin():
        student.delete()

    resp = APIClient().post("/api/v1/notifications/unsubscribe/", {"token": token}, format="json")
    assert resp.status_code == 200  # a deleted account receives nothing anyway
    assert resp.json()["category"] == NotificationCategory.NEW_SCHOOLS


# ---------------------------------------------------------------------------
# P3 — GDPR export now covers the Epic 8 tables
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_gdpr_export_includes_notifications_domain():
    import json

    from apps.accounts.exporters import _REGISTRY

    student = _mk_student("export-notif@test.local")
    with as_path_admin():
        NotificationPreference.objects.create(
            user=student, category=NotificationCategory.NEW_SCHOOLS, enabled=False
        )
        DeltaRecapCursor.objects.create(user=student, seen_at=timezone.now())

    assert "notifications" in _REGISTRY
    entries = list(_REGISTRY["notifications"](student))
    assert entries[0].archive_path == "notifications/notifications.json"
    payload = json.loads(entries[0].content)
    by_cat = {p["category"]: p for p in payload["preferences"]}
    assert by_cat[NotificationCategory.NEW_SCHOOLS]["enabled"] is False
    assert by_cat[NotificationCategory.PARCOURSUP_CALENDAR]["enabled"] is True
    assert payload["delta_recap_seen_at"] is not None


# ---------------------------------------------------------------------------
# Beat wiring (P0-2 / P1-1) — the schedule actually references the tasks
# ---------------------------------------------------------------------------


def test_maintenance_tasks_are_scheduled():
    from path_advisor.celery import app

    scheduled = {entry["task"] for entry in app.conf.beat_schedule.values()}
    assert "mailer.prune_email_outbox" in scheduled
    assert "telemetry.prune_rum_vitals" in scheduled
    assert "mailer.sweep_stale_outbox" in scheduled
