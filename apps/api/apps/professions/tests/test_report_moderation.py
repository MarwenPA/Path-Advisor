"""Story 9.3 — moderation queue + workflow.

Contracts: oldest-first queue with per-row `overdue` (> 7 j) and a global
counter; resolve notifies the reporter through the 8.2 engine (opt-out
honoured); dismiss REQUIRES a reason and stays silent; request-info
REQUIRES a message, notifies it, and keeps the report in the queue; every
transition writes handled_by/at + an audit row; the two new templates pass
the shared tone lint.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.audit.tests.factories import PathAdminUserFactory
from apps.core.rls_testing import as_path_admin
from apps.notifications.models import NotificationCategory, NotificationPreference
from apps.notifications.tone import URGENCY_MARKERS
from apps.professions.models import Profession, ProfessionReport

QUEUE_URL = "/api/v1/admin/professions/reports/"


@pytest.fixture
def admin(db):
    return PathAdminUserFactory(email="karim-93@test.local", email_verified_at=timezone.now())


@pytest.fixture
def client(admin) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


def _mk_report(*, email: str, age_days: int = 0, **overrides) -> ProfessionReport:
    with as_path_admin():
        reporter = User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    profession, _ = Profession.objects.get_or_create(
        slug="metier-signale-93",
        defaults=dict(
            name="Métier Signalé",
            description="x" * 120,
            daily_routine="x" * 90,
            prospects_text="a. b. c.",
            is_active=True,
        ),
    )
    report = ProfessionReport.objects.create(
        profession=profession,
        reporter=reporter,
        error_type=ProfessionReport.ErrorType.DEBOUCHES_PERIMES,
        comment="Les débouchés datent de 2019.",
        **overrides,
    )
    if age_days:
        ProfessionReport.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - timedelta(days=age_days)
        )
        report.refresh_from_db()
    return report


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_queue_is_oldest_first_with_overdue_flags(client):
    fresh = _mk_report(email="frais-93@test.local", age_days=1)
    stale = _mk_report(email="vieux-93@test.local", age_days=10)
    resolved = _mk_report(email="resolu-93@test.local", age_days=20, status="resolved")

    data = client.get(QUEUE_URL).json()
    ids = [row["id"] for row in data["results"]]
    assert ids == [stale.pk, fresh.pk]  # oldest first, resolved excluded
    assert resolved.pk not in ids
    by_id = {row["id"]: row for row in data["results"]}
    assert by_id[stale.pk]["overdue"] is True  # the 7-day SLA alert
    assert by_id[fresh.pk]["overdue"] is False
    assert data["overdue_count"] == 1


@pytest.mark.django_db
def test_queue_refuses_non_admin(db):
    with as_path_admin():
        student = User.objects.create_user(
            email="intrus-93@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    c = APIClient()
    c.force_authenticate(user=student)
    assert c.get(QUEUE_URL).status_code == 403


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_resolve_notifies_the_reporter(client, django_capture_on_commit_callbacks):
    report = _mk_report(email="resolu-notif-93@test.local")

    with django_capture_on_commit_callbacks(execute=True):
        resp = client.post(f"{QUEUE_URL}{report.pk}/resolve/", {"note": "Débouchés actualisés."})
    assert resp.status_code == 200

    report.refresh_from_db()
    assert report.status == ProfessionReport.Status.RESOLVED
    assert report.handled_by is not None and report.handled_at is not None
    assert AuditLog.objects.filter(action="moderation.report_resolved").exists()
    assert len(mail.outbox) == 1
    assert "mise à jour" in mail.outbox[0].subject
    assert "/desinscription/" in mail.outbox[0].body  # engine footer rode along


@pytest.mark.django_db(transaction=True)
def test_resolve_respects_opt_out(client, django_capture_on_commit_callbacks):
    report = _mk_report(email="optout-93@test.local")
    with as_path_admin():
        NotificationPreference.objects.create(
            user=report.reporter, category=NotificationCategory.REPORT_UPDATES, enabled=False
        )

    with django_capture_on_commit_callbacks(execute=True):
        client.post(f"{QUEUE_URL}{report.pk}/resolve/")

    report.refresh_from_db()
    assert report.status == ProfessionReport.Status.RESOLVED  # the WORK happened
    assert len(mail.outbox) == 0  # the email respected the student's choice


@pytest.mark.django_db(transaction=True)
def test_dismiss_requires_a_reason_and_stays_silent(client, django_capture_on_commit_callbacks):
    report = _mk_report(email="rejet-93@test.local")

    resp = client.post(f"{QUEUE_URL}{report.pk}/dismiss/", {"reason": "  "})
    assert resp.status_code == 400
    report.refresh_from_db()
    assert report.status == ProfessionReport.Status.PENDING  # untouched

    with django_capture_on_commit_callbacks(execute=True):
        resp = client.post(
            f"{QUEUE_URL}{report.pk}/dismiss/", {"reason": "Information déjà à jour."}
        )
    assert resp.status_code == 200
    report.refresh_from_db()
    assert report.status == ProfessionReport.Status.DISMISSED
    assert report.admin_note == "Information déjà à jour."
    assert len(mail.outbox) == 0  # deliberate silence (§2.4)


@pytest.mark.django_db(transaction=True)
def test_request_info_notifies_and_keeps_in_queue(client, django_capture_on_commit_callbacks):
    report = _mk_report(email="precision-93@test.local")

    with django_capture_on_commit_callbacks(execute=True):
        resp = client.post(
            f"{QUEUE_URL}{report.pk}/request-info/",
            {"message": "Peux-tu préciser quelle section te semble périmée ?"},
        )
    assert resp.status_code == 200

    report.refresh_from_db()
    assert report.status == ProfessionReport.Status.INFO_REQUESTED
    assert len(mail.outbox) == 1
    assert "quelle section te semble périmée" in mail.outbox[0].body
    # Still in the actionable queue.
    ids = [row["id"] for row in client.get(QUEUE_URL).json()["results"]]
    assert report.pk in ids


# ---------------------------------------------------------------------------
# Catégorie + ton
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_report_updates_category_is_now_visible_in_settings(client, db):
    """It has an emitter from birth — the 9.1/P2-4 rule keeps it listed."""
    with as_path_admin():
        student = User.objects.create_user(
            email="reglages-93@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    c = APIClient()
    c.force_authenticate(user=student)
    categories = {
        p["category"] for p in c.get("/api/v1/me/notification-preferences/").json()["preferences"]
    }
    assert "report_updates" in categories
    assert "profile_completion" not in categories  # still emitterless, still hidden


@pytest.mark.parametrize("base", ["report_resolved", "report_info_requested"])
def test_report_templates_pass_the_shared_tone_lint(base):
    context = {
        "profession_name": "Métier Signalé",
        "fiche_url": "https://path-advisor.fr/metiers/metier-signale-93",
        "admin_message": "Peux-tu préciser la section concernée ?",
        "category_label": "Suivi de tes signalements",
        "manage_notifications_url": "https://path-advisor.fr/parametres/notifications",
        "unsubscribe_url": "https://path-advisor.fr/desinscription/x",
    }
    rendered = "\n".join(
        [
            render_to_string(f"notifications/email/{base}_subject.txt", context),
            render_to_string(f"notifications/email/{base}.txt", context),
            render_to_string(f"notifications/email/{base}.html", context),
        ]
    ).lower()
    for pattern in URGENCY_MARKERS:
        assert re.search(pattern, rendered) is None, f"banned marker {pattern!r} in {base}"
