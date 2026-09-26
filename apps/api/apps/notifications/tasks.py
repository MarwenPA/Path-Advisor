"""Story 8.3 — daily Parcoursup-calendar dispatch (beat).

One batch per milestone, exactly once: `notified_at` is set inside the same
transaction that creates the outbox rows — a crash before commit sends
nothing and marks nothing; after commit, every email is durably queued
(8.1) and per-user opt-out was already honoured by the engine (8.2).

Cross-user audience read runs under `with_system_actor` — the documented
escape hatch for beat tasks that act on behalf of the platform (see
`core/rls.py`; distinct from an anonymous bypass for forensics).
"""

from __future__ import annotations

import os
from datetime import timedelta

import structlog
from celery import shared_task
from django.db import OperationalError, transaction
from django.utils import timezone
from django.utils.formats import date_format

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import with_system_actor

from .milestone_copy import MILESTONE_COPY
from .models import (
    MilestoneKind,
    NotificationCategory,
    NotificationPreference,
    ParcoursupMilestone,
)
from .services import notify

log = structlog.get_logger(__name__)

#: Story 8.3 audience: élèves in Terminale or post-bac (AC1).
AUDIENCE_LEVELS = ("lycee_terminale", "postbac")


def _site_url() -> str:
    return os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")


@shared_task(name="notifications.send_parcoursup_milestone_notifications")
def send_parcoursup_milestone_notifications() -> int:
    """Send every due, un-notified milestone. Returns emails queued."""
    today = timezone.localdate()
    queued = 0

    with with_system_actor(reason="notifications.parcoursup_calendar_beat"):
        candidates = list(
            ParcoursupMilestone.objects.filter(notified_at__isnull=True).order_by("date")
        )

        # Revue Epic 8 (P1-5): a milestone whose date already passed must
        # never be announced in the present tense ("la plateforme ouvre
        # le 20 janvier"… sent on the 25th). Mark it consumed, loudly.
        for milestone in [m for m in candidates if m.date < today]:
            claimed = ParcoursupMilestone.objects.filter(
                pk=milestone.pk, notified_at__isnull=True
            ).update(notified_at=timezone.now())
            if claimed:
                log.error(
                    "notifications.parcoursup_milestone_missed",
                    kind=milestone.kind,
                    campaign=milestone.campaign,
                    date=str(milestone.date),
                )

        due = [
            m
            for m in candidates
            if m.date >= today and (m.date - timedelta(days=m.notify_days_before)) <= today
        ]

        # Batch the opt-out reads once per run (scale note, revue Epic 8):
        # `notify()` re-checks per user — this only avoids the render/token
        # work for known opt-outs, it never replaces the enforcement point.
        opted_out = set(
            NotificationPreference.objects.filter(
                category=NotificationCategory.PARCOURSUP_CALENDAR, enabled=False
            ).values_list("user_id", flat=True)
        )

        for milestone in due:
            copy = MILESTONE_COPY[MilestoneKind(milestone.kind)]
            date_fr = date_format(milestone.date, "j F Y")
            recipients = list(
                User.objects.filter(
                    role=UserRole.STUDENT,
                    status=UserStatus.ACTIVE,
                    email_verified_at__isnull=False,
                    # `level` lives on the LevelProfile ONE-TO-ONE hanging off
                    # StudentProfile (related_name chain verified in
                    # students/models.py — a naive student_profile__level
                    # would silently match nobody).
                    student_profile__level_profile__level__in=AUDIENCE_LEVELS,
                ).values_list("id", "email")
            )

            queued_milestone = 0
            with transaction.atomic():
                # Revue Epic 8 (P0-1): claim the milestone ATOMICALLY at the
                # top of the transaction. Two concurrent runs (beat backlog
                # after a worker outage x --concurrency=2, or beat + manual
                # `celery call`) both used to read `notified_at IS NULL` and
                # both sent — a mass double-send to minors. The conditional
                # UPDATE makes the second run block on the row lock, then
                # see 0 rows and skip. Crash mid-loop still rolls the claim
                # back with the outbox rows (same transaction).
                claimed = ParcoursupMilestone.objects.filter(
                    pk=milestone.pk, notified_at__isnull=True
                ).update(notified_at=timezone.now())
                if not claimed:
                    log.info(
                        "notifications.parcoursup_milestone_already_claimed",
                        kind=milestone.kind,
                        campaign=milestone.campaign,
                    )
                    continue
                for user_id, email in recipients:
                    if user_id in opted_out:
                        continue
                    row = notify(
                        user_id=user_id,
                        email=email,
                        category=NotificationCategory.PARCOURSUP_CALENDAR,
                        template_app="notifications",
                        template_base="email/parcoursup_milestone",
                        context={
                            "subject": str(copy["subject"]).format(date=date_fr),
                            "intro": str(copy["intro"]).format(date=date_fr),
                            "checklist": copy["checklist"],
                            "cta_label": copy["cta_label"],
                            "cta_url": f"{_site_url()}{copy['cta_path']}",
                        },
                    )
                    if row is not None:
                        queued_milestone += 1

            queued += queued_milestone
            log.info(
                "notifications.parcoursup_milestone_dispatched",
                kind=milestone.kind,
                campaign=milestone.campaign,
                recipients=len(recipients),
                # Per-milestone counter (revue Epic 8, ops fix): the old log
                # reported the cross-milestone running total.
                queued=queued_milestone,
            )

    return queued


#: Story 8.5 — minimum cumulated signal overlaps (passions + valeurs +
#: spécialités) for a new school's target profession to count as relevant.
#: Honest scope (revue Epic 8, P2-3): these are THREE of Story 3.3's FIVE
#: scoring dimensions — `niveau_compatibility` and `bulletin_quality` are
#: deliberately left out (the full scored ranking calls the ai-service per
#: student over HTTP, which a weekly batch must not do: N network calls +
#: an outage would sink the digest). "Correspond à ton profil" therefore
#: means signal affinity, not admission likelihood — consigned in the
#: story doc §2.
OVERLAP_MIN = 2

DIGEST_WINDOW_DAYS = 7
DIGEST_MAX_SCHOOLS_LISTED = 5


def _signal_overlap(profile_signals: dict, profession_signals: dict) -> int:
    total = 0
    for key in ("passions", "valeurs", "specialites"):
        mine = set(profile_signals.get(key) or [])
        theirs = set(profession_signals.get(key) or [])
        total += len(mine & theirs)
    return total


@shared_task(
    name="notifications.send_new_schools_digest",
    # Revue Epic 8 (P3): the beat fires ONCE a week — a transient blip
    # (DB restart, broker hiccup) at 08:00 Monday must not silently cost
    # the whole week. Safe to retry: the `week` unique row makes a
    # replayed run exactly-once.
    autoretry_for=(OperationalError, ConnectionError, TimeoutError),
    retry_kwargs={"max_retries": 3, "countdown": 300},
)
def send_new_schools_digest() -> int:
    """Story 8.5 — weekly digest of newly-added relevant schools.

    Exactly-once per ISO week via `NewSchoolsDigestRun` (a same-week re-run
    or retry sends nothing). Work is proportional to the NEW schools, never
    to the whole catalog: new schools → their parcours' professions → local
    signal overlap per student.
    """
    from apps.schools.models import Parcours, School

    from .models import NewSchoolsDigestRun

    today = timezone.localdate()
    week = f"{today.isocalendar().year}-W{today.isocalendar().week:02d}"
    if NewSchoolsDigestRun.objects.filter(week=week).exists():
        log.info("notifications.new_schools_digest_already_ran", week=week)
        return 0

    queued = 0
    with with_system_actor(reason="notifications.new_schools_digest_beat"):
        # Revue Epic 8 (P2-2): anchor the window on the LAST run instead of
        # `now()-7d` — execution jitter between two Mondays used to leave a
        # gap (a school created between run N and run N+1 - 7d was never
        # digested) or an overlap (same schools cited twice). Contiguous by
        # construction now; this also supersedes the 8.5 §2.2 "a skipped
        # week is lost" limitation — a late run catches the backlog up.
        last_run = NewSchoolsDigestRun.objects.order_by("-sent_at").first()
        since = (
            last_run.sent_at
            if last_run is not None
            else timezone.now() - timedelta(days=DIGEST_WINDOW_DAYS)
        )
        new_schools = list(School.objects.filter(is_active=True, created_at__gte=since))
        if not new_schools:
            NewSchoolsDigestRun.objects.create(week=week, emails_queued=0)
            return 0

        # school → the professions its parcours lead to (with their signals).
        parcours = Parcours.objects.filter(
            target_school__in=new_schools, profession__is_active=True
        ).select_related("profession", "target_school")
        # Keys uniformly str(): the FK pk type differs across models in this
        # codebase (char ids vs autoids) and mypy rightly refuses the union.
        school_professions: dict[str, list] = {}
        for p in parcours:
            school_professions.setdefault(str(p.target_school_id), []).append(p.profession)

        opted_out = set(
            NotificationPreference.objects.filter(
                category=NotificationCategory.NEW_SCHOOLS, enabled=False
            ).values_list("user_id", flat=True)
        )

        students = User.objects.filter(
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at__isnull=False,
            student_profile__isnull=False,
        ).select_related("student_profile__level_profile")

        with transaction.atomic():
            for student in students:
                if student.id in opted_out:
                    continue
                profile = student.student_profile
                level = getattr(profile, "level_profile", None)
                profile_signals = {
                    "passions": profile.passions,
                    "valeurs": profile.valeurs,
                    "specialites": (level.specialites if level else []) or [],
                }
                matches: list[tuple[School, str]] = []
                for school in new_schools:
                    best = 0
                    best_name = ""
                    for prof in school_professions.get(str(school.id), []):
                        overlap = _signal_overlap(profile_signals, prof.signals_json or {})
                        if overlap > best:
                            best, best_name = overlap, prof.name
                    if best >= OVERLAP_MIN:
                        matches.append((school, best_name))
                if not matches:
                    continue
                listed = matches[:DIGEST_MAX_SCHOOLS_LISTED]
                # Revue Epic 8 (P3): name a profession in the subject ONLY
                # when every matched school points at the same one — an
                # arbitrary first-school pick reads as a mistargeted email
                # ("je n'ai jamais visé ce métier"). Empty = generic subject.
                distinct_professions = {name for _, name in matches}
                subject_profession = listed[0][1] if len(distinct_professions) == 1 else ""
                row = notify(
                    user_id=student.id,
                    email=student.email,
                    category=NotificationCategory.NEW_SCHOOLS,
                    template_app="notifications",
                    template_base="email/new_schools_digest",
                    context={
                        "count": len(matches),
                        "profession_name": subject_profession,
                        "schools": [
                            {"name": s.name, "city": s.city, "profession": pname}
                            for s, pname in listed
                        ],
                        "more_count": max(0, len(matches) - len(listed)),
                        "explore_url": f"{_site_url()}/schools",
                    },
                )
                if row is not None:
                    queued += 1
            NewSchoolsDigestRun.objects.create(week=week, emails_queued=queued)

    log.info("notifications.new_schools_digest_sent", week=week, queued=queued)
    return queued
