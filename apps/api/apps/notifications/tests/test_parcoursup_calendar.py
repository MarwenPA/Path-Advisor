"""Story 8.3 — calendar dispatch + the executable anti-urgency contract.

UX-DR28 is a TEST here, not a style guide: every milestone's rendered
subject/text/HTML is linted against urgency markers. A future copy edit
that sneaks in « dernière chance » fails CI.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.mailer.models import EmailOutbox
from apps.notifications.milestone_copy import MILESTONE_COPY
from apps.notifications.models import (
    MilestoneKind,
    NotificationCategory,
    NotificationPreference,
    ParcoursupMilestone,
)
from apps.notifications.tasks import send_parcoursup_milestone_notifications

#: UX-DR28 — urgency markers banned from every rendered variant. Kept as
#: regexes so « Plus que 18 jours » and « plus que 3 jours » both trip it.
# Revue Epic 8: the banned list is shared (apps.notifications.tone) so the
# lints can never drift between stories again.
from apps.notifications.tone import URGENCY_MARKERS as BANNED
from apps.students.models import StudentLevelProfile, StudentProfile


def _mk_student(email: str, level: str | None = "lycee_terminale") -> User:
    with as_path_admin():
        user = User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        profile = StudentProfile.objects.create(user=user)
        if level is not None:
            StudentLevelProfile.objects.create(profile=profile, level=level)
    return user


def _mk_milestone(**overrides) -> ParcoursupMilestone:
    fields = {
        "kind": MilestoneKind.OUVERTURE,
        "campaign": "2026-2027",
        "date": timezone.localdate() + timedelta(days=18),
        "notify_days_before": 18,
        **overrides,
    }
    return ParcoursupMilestone.objects.create(**fields)


# ---------------------------------------------------------------------------
# UX-DR28 — executable anti-urgency lint over EVERY milestone's rendering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", list(MilestoneKind))
def test_rendered_copy_carries_no_urgency(kind):
    copy = MILESTONE_COPY[kind]
    context = {
        "subject": str(copy["subject"]).format(date="12 mars 2027"),
        "intro": str(copy["intro"]).format(date="12 mars 2027"),
        "checklist": copy["checklist"],
        "cta_label": copy["cta_label"],
        "cta_url": "https://path-advisor.fr/mes-paris",
        "category_label": "Calendrier Parcoursup",
        "manage_notifications_url": "https://path-advisor.fr/parametres/notifications",
        "unsubscribe_url": "https://path-advisor.fr/desinscription/x",
    }
    rendered = "\n".join(
        [
            context["subject"],
            render_to_string("notifications/email/parcoursup_milestone.txt", context),
            render_to_string("notifications/email/parcoursup_milestone.html", context),
        ]
    ).lower()
    for pattern in BANNED:
        assert re.search(pattern, rendered) is None, f"urgency marker {pattern!r} in {kind}"
    # The mandated stance: preparation, not pressure (AC1/AC2).
    assert "préparer" in rendered
    # Calm CTAs only (AC3).
    assert copy["cta_label"] in ("Revoir mes paris", "Compléter mon profil")


def test_all_five_standard_milestones_have_copy_and_seed():
    assert set(MILESTONE_COPY) == set(MilestoneKind)  # AC2: the 5 jalons
    for copy in MILESTONE_COPY.values():
        assert len(copy["checklist"]) >= 3  # a real, non-blocking checklist


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_due_milestone_notifies_audience_once(django_capture_on_commit_callbacks):
    terminale = _mk_student("terminale@test.local", "lycee_terminale")
    _mk_student("seconde@test.local", "lycee_2nde")  # out of audience
    _mk_student("sans-niveau@test.local", None)  # no level profile at all
    milestone = _mk_milestone()

    with django_capture_on_commit_callbacks(execute=True):
        queued = send_parcoursup_milestone_notifications()

    assert queued == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [terminale.email]
    body = mail.outbox[0].body
    assert "préparer" in body
    assert "/desinscription/" in body  # the 8.2 engine's legal footer rode along

    milestone.refresh_from_db()
    assert milestone.notified_at is not None
    # Second run: nothing new — batch-level dedup.
    with django_capture_on_commit_callbacks(execute=True):
        assert send_parcoursup_milestone_notifications() == 0
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
def test_not_due_milestone_stays_silent(django_capture_on_commit_callbacks):
    _mk_student("terminale2@test.local")
    _mk_milestone(date=timezone.localdate() + timedelta(days=40), notify_days_before=18)
    with django_capture_on_commit_callbacks(execute=True):
        assert send_parcoursup_milestone_notifications() == 0
    assert EmailOutbox.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_opted_out_student_is_skipped_by_the_engine(django_capture_on_commit_callbacks):
    student = _mk_student("optout@test.local")
    with as_path_admin():
        NotificationPreference.objects.create(
            user=student,
            category=NotificationCategory.PARCOURSUP_CALENDAR,
            enabled=False,
        )
    milestone = _mk_milestone()
    with django_capture_on_commit_callbacks(execute=True):
        assert send_parcoursup_milestone_notifications() == 0
    assert len(mail.outbox) == 0
    milestone.refresh_from_db()
    assert milestone.notified_at is not None  # the batch still completes


@pytest.mark.django_db
def test_seed_command_is_idempotent():
    call_command("seed_parcoursup_calendar")
    assert ParcoursupMilestone.objects.count() == 5
    call_command("seed_parcoursup_calendar")
    assert ParcoursupMilestone.objects.count() == 5  # no duplicates
    kinds = set(ParcoursupMilestone.objects.values_list("kind", flat=True))
    assert kinds == set(MilestoneKind.values)  # AC2
