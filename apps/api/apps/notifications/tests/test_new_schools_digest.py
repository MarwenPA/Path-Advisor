"""Story 8.5 — weekly new-schools digest.

Contracts: relevance = LOCAL signal overlap on 3.3's criteria dimensions
(never an ai-service call in the batch), grouping with a counter (AC2),
exactly-once per ISO week, opt-out via the engine, calm tone.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.notifications.models import (
    NewSchoolsDigestRun,
    NotificationCategory,
    NotificationPreference,
)
from apps.notifications.tasks import OVERLAP_MIN, _signal_overlap, send_new_schools_digest
from apps.professions.models import Profession
from apps.schools.models import Parcours, School
from apps.students.models import StudentLevelProfile, StudentProfile


def _mk_student(email: str, *, passions=(), valeurs=(), specialites=()) -> User:
    with as_path_admin():
        user = User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        profile = StudentProfile.objects.create(
            user=user, passions=list(passions), valeurs=list(valeurs)
        )
        StudentLevelProfile.objects.create(
            profile=profile, level="lycee_terminale", specialites=list(specialites)
        )
    return user


def _mk_school_with_profession(slug: str, *, signals: dict) -> School:
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
    profession = Profession.objects.create(
        slug=f"metier-{slug}",
        name=f"Métier {slug}",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
        signals_json=signals,
    )
    Parcours.objects.create(
        profession=profession,
        target_school=school,
        niveau_scolaire="terminale_generale",
        label="Voie test",
    )
    return school


MATCHING_SIGNALS = {
    "passions": ["sciences", "robotique"],
    "valeurs": ["autonomie"],
    "specialites": [],
}


# ---------------------------------------------------------------------------
# Relevance rule — 3.3's criteria, locally
# ---------------------------------------------------------------------------


def test_signal_overlap_counts_across_dimensions():
    profile = {"passions": ["sciences"], "valeurs": ["autonomie"], "specialites": ["maths"]}
    assert _signal_overlap(profile, MATCHING_SIGNALS) == 2  # sciences + autonomie
    assert _signal_overlap(profile, {"passions": ["cinema"]}) == 0
    assert _signal_overlap({}, MATCHING_SIGNALS) == 0  # empty profile never matches
    assert OVERLAP_MIN == 2  # the documented threshold


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_digest_groups_and_counts(django_capture_on_commit_callbacks):
    matched = _mk_student("match@test.local", passions=["sciences"], valeurs=["autonomie"])
    _mk_student("nomatch@test.local", passions=["cinema"])  # 0 overlap → silent
    for i in range(3):
        _mk_school_with_profession(f"nouvelle-{i}", signals=MATCHING_SIGNALS)

    with django_capture_on_commit_callbacks(execute=True):
        queued = send_new_schools_digest()

    assert queued == 1  # ONE digest, not three emails (AC2)
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == [matched.email]
    assert "3 nouvelles écoles correspondent" in msg.subject  # the counter, AC2
    assert "/desinscription/" in msg.body  # engine footer

    run = NewSchoolsDigestRun.objects.get()
    assert run.emails_queued == 1


@pytest.mark.django_db(transaction=True)
def test_same_week_rerun_sends_nothing(django_capture_on_commit_callbacks):
    _mk_student("match2@test.local", passions=["sciences"], valeurs=["autonomie"])
    _mk_school_with_profession("nouvelle-x", signals=MATCHING_SIGNALS)

    with django_capture_on_commit_callbacks(execute=True):
        assert send_new_schools_digest() == 1
        # Retry / manual re-run inside the same ISO week: exactly-once.
        assert send_new_schools_digest() == 0
    assert len(mail.outbox) == 1
    assert NewSchoolsDigestRun.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_old_schools_are_not_news(django_capture_on_commit_callbacks):
    _mk_student("match3@test.local", passions=["sciences"], valeurs=["autonomie"])
    school = _mk_school_with_profession("ancienne", signals=MATCHING_SIGNALS)
    School.objects.filter(pk=school.pk).update(created_at=timezone.now() - timedelta(days=30))

    with django_capture_on_commit_callbacks(execute=True):
        assert send_new_schools_digest() == 0
    assert len(mail.outbox) == 0
    # The week is still marked ran — an empty week is a completed week.
    assert NewSchoolsDigestRun.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_opted_out_student_is_skipped(django_capture_on_commit_callbacks):
    student = _mk_student("optout5@test.local", passions=["sciences"], valeurs=["autonomie"])
    with as_path_admin():
        NotificationPreference.objects.create(
            user=student, category=NotificationCategory.NEW_SCHOOLS, enabled=False
        )
    _mk_school_with_profession("nouvelle-oo", signals=MATCHING_SIGNALS)

    with django_capture_on_commit_callbacks(execute=True):
        assert send_new_schools_digest() == 0
    assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# Tone — same executable-calm contract as 8.3/8.4
# ---------------------------------------------------------------------------

BANNED = [
    r"derni[eè]re chance",
    r"plus que \d+",
    r"\bvite\b",
    r"\burgent",
    r"!!",
    r"ne (rate|manque) pas",
]


@pytest.mark.parametrize("count", [1, 5])
def test_digest_copy_is_calm_and_agrees_in_french(count):
    context = {
        "count": count,
        "profession_name": "ingénieure biomédicale",
        "schools": [{"name": "INSA Lyon", "city": "Lyon", "profession": "Ingénieure biomédicale"}],
        "more_count": 0,
        "explore_url": "https://path-advisor.fr/schools",
        "category_label": "Nouvelles écoles pertinentes",
        "manage_notifications_url": "https://path-advisor.fr/parametres/notifications",
        "unsubscribe_url": "https://path-advisor.fr/desinscription/x",
    }
    subject = render_to_string(
        "notifications/email/new_schools_digest_subject.txt", context
    ).strip()
    rendered = "\n".join(
        [
            subject,
            render_to_string("notifications/email/new_schools_digest.txt", context),
            render_to_string("notifications/email/new_schools_digest.html", context),
        ]
    ).lower()
    for pattern in BANNED:
        assert re.search(pattern, rendered) is None, f"urgency marker {pattern!r}"
    # French agreement both ways (the AC's own example wording at 5).
    if count == 1:
        assert subject.startswith("1 nouvelle école correspond ")
    else:
        assert subject.startswith("5 nouvelles écoles correspondent ")
