"""Story 8.4 — school-response notification through the engine.

Three contracts: the email now respects the student's opt-out (AC3), the
response stays recorded in-app regardless (AC3), and the "not aligned"
copy is diplomatic BY TEST — same executable-tone approach as 8.3's
UX-DR28 lint.
"""

from __future__ import annotations

import re

import pytest
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.mailer.models import EmailOutbox
from apps.notifications.models import NotificationCategory, NotificationPreference
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachResponse
from apps.outreach.services.school_response import respond_to_outreach_request
from apps.professions.models import Profession
from apps.schools.models import School


@pytest.fixture
def outreach_request(db) -> EarlyOutreachRequest:
    # Même patron de fixtures que test_school_response.py (bypass_rls nominal
    # de setup) — recréé localement plutôt qu'importé d'un module de tests.
    with bypass_rls(reason="test_setup.create_response_user"):
        student = User.objects.create_user(
            email="eleve-notif-84@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    school = School.objects.create(
        slug="ecole-notif-84",
        name="École Notif 8.4",
        type=School.Type.ECOLE_INGENIEUR,
        city="Lyon",
        region="ARA",
        postal_code="69000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
    )
    profession = Profession.objects.create(
        slug="metier-notif-84",
        name="Métier Notif 8.4",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )
    with bypass_rls(reason="test_setup.create_outreach"):
        return EarlyOutreachRequest.objects.create(
            student=student,
            school=school,
            profession=profession,
        )


#: AC2 (« conformité émotionnelle ») — shared list (revue Epic 8).
from apps.notifications.tone import NOT_ALIGNED_MARKERS as BANNED_NOT_ALIGNED  # noqa: E402


def _render_response(action: str, comment: str = "") -> str:
    context = {
        "school": {"name": "INSA Lyon"},
        "outreach": {"id": "eor_x", "profession": {"name": "Ingénieur biomédical"}},
        "response": {"action": action, "comment": comment},
        "response_url": "https://path-advisor.fr/mes-envois/eor_x",
        "explore_url": "https://path-advisor.fr/schools",
        "category_label": "Réponses école",
        "manage_notifications_url": "https://path-advisor.fr/parametres/notifications",
        "unsubscribe_url": "https://path-advisor.fr/desinscription/x",
    }
    return "\n".join(
        [
            render_to_string("outreach/email/school_responded_subject.txt", context),
            render_to_string("outreach/email/school_responded.txt", context),
            render_to_string("outreach/email/school_responded.html", context),
        ]
    )


# ---------------------------------------------------------------------------
# Tone — executable, not aspirational
# ---------------------------------------------------------------------------


def test_not_aligned_copy_is_diplomatic_and_offers_alternatives():
    rendered = _render_response("not_aligned")
    low = rendered.lower()
    for pattern in BANNED_NOT_ALIGNED:
        assert re.search(pattern, low) is None, f"banned tone {pattern!r} in not_aligned copy"
    # AC2's required stance: an alternative path, explicitly.
    assert "explorer d'autres écoles" in low
    assert "profil similaire" in low
    # AC1's CTA.
    assert "Voir la réponse" in rendered
    assert "/mes-envois/eor_x" in rendered


@pytest.mark.parametrize("action", ["interested", "not_aligned", "interview_requested"])
def test_every_variant_carries_the_legal_footer_and_cta(action):
    rendered = _render_response(action)
    assert "/parametres/notifications" in rendered
    assert "/desinscription/" in rendered
    assert "/mes-envois/eor_x" in rendered


# ---------------------------------------------------------------------------
# Engine wiring — opt-out honoured, response still recorded (AC3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_opted_out_student_gets_no_email_but_response_persists(
    outreach_request, django_capture_on_commit_callbacks
):
    student = outreach_request.student
    NotificationPreference.objects.create(
        user=student,
        category=NotificationCategory.SCHOOL_RESPONSES,
        enabled=False,
    )

    with django_capture_on_commit_callbacks(execute=True):
        respond_to_outreach_request(
            outreach=outreach_request, action="not_aligned", comment="Merci de ta candidature."
        )

    assert len(mail.outbox) == 0
    assert EmailOutbox.objects.count() == 0
    # AC3 « la notification reste visible in-app » : la réponse EST là —
    # /mes-envois (Story 5.9) la lit depuis cette table, l'email n'était
    # qu'un canal.
    assert EarlyOutreachResponse.objects.filter(request=outreach_request).exists()


@pytest.mark.django_db(transaction=True)
def test_default_student_receives_engine_email_with_footer(
    outreach_request, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        respond_to_outreach_request(outreach=outreach_request, action="interested")

    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "/desinscription/" in body  # engine footer rode along
    assert "/mes-envois/" in body  # AC1 CTA
