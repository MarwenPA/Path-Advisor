"""Story 8.6 — DeltaRecap cards + cursor semantics.

Contracts under test: baseline on first GET (zero cards, cursor created),
the 24 h J+1 rule, one card per school response WITH the 5.8 before/after
stat, the aggregated new-schools card (same overlap rule as the 8.5
digest), the calendar card inside its `notify_days_before` window, ACK
moving the cursor, and the executable calm-tone lint over EVERY card the
backend can produce (8.3 urgency markers + 8.4 not-aligned markers).
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.notifications.delta_recap import _RESPONSE_COPY, compute_cards
from apps.notifications.models import DeltaRecapCursor, MilestoneKind, ParcoursupMilestone
from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachResponse,
    EarlyOutreachResponseAction,
)
from apps.professions.models import Profession
from apps.schools.models import AdmissionStat, Parcours, School
from apps.students.models import StudentLevelProfile, StudentProfile

RECAP_URL = "/api/v1/me/delta-recap/"
ACK_URL = "/api/v1/me/delta-recap/ack/"

MATCHING_SIGNALS = {
    "passions": ["sciences", "robotique"],
    "valeurs": ["autonomie"],
    "specialites": [],
}


@pytest.fixture
def student(db):
    with as_path_admin():
        user = User.objects.create_user(
            email="eleve-delta@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        profile = StudentProfile.objects.create(
            user=user, passions=["sciences"], valeurs=["autonomie"]
        )
        StudentLevelProfile.objects.create(profile=profile, level="lycee_terminale")
    return user


@pytest.fixture
def client(student):
    c = APIClient()
    c.force_authenticate(user=student)
    return c


def _age_cursor(user, *, days: int) -> None:
    """Backdate the cursor so the J+1 rule passes and `since` is in the past."""
    DeltaRecapCursor.objects.update_or_create(
        user=user, defaults={"seen_at": timezone.now() - timedelta(days=days)}
    )


def _mk_school(slug: str) -> School:
    return School.objects.create(
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


def _mk_response(student, school: School, action: str) -> EarlyOutreachResponse:
    profession = Profession.objects.create(
        slug=f"metier-{school.slug}",
        name=f"Métier {school.slug}",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )
    with as_path_admin():
        request = EarlyOutreachRequest.objects.create(
            student=student, school=school, profession=profession
        )
        return EarlyOutreachResponse.objects.create(request=request, action=action)


# ---------------------------------------------------------------------------
# Cursor semantics
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_first_get_creates_baseline_and_returns_no_cards(client, student):
    assert not DeltaRecapCursor.objects.filter(user=student).exists()
    resp = client.get(RECAP_URL)
    assert resp.status_code == 200
    assert resp.json() == {"cards": []}
    assert DeltaRecapCursor.objects.filter(user=student).exists()


@pytest.mark.django_db
def test_cursor_younger_than_24h_returns_no_cards(client, student):
    # Deltas EXIST, but the return is same-day: UX-DR29 says J+1 or more.
    _age_cursor(student, days=0)
    _mk_response(student, _mk_school("meme-jour"), EarlyOutreachResponseAction.INTERESTED)
    assert client.get(RECAP_URL).json() == {"cards": []}


@pytest.mark.django_db
def test_get_does_not_move_the_cursor_ack_does(client, student):
    _age_cursor(student, days=30)
    before = DeltaRecapCursor.objects.get(user=student).seen_at
    client.get(RECAP_URL)
    assert DeltaRecapCursor.objects.get(user=student).seen_at == before  # unseen = still news
    assert client.post(ACK_URL).status_code == 204
    assert DeltaRecapCursor.objects.get(user=student).seen_at > before


@pytest.mark.django_db
def test_anonymous_is_rejected(db):
    assert APIClient().get(RECAP_URL).status_code in (401, 403)
    assert APIClient().post(ACK_URL).status_code in (401, 403)


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_school_response_card_carries_before_after_stat(client, student):
    _age_cursor(student, days=30)
    school = _mk_school("insa-delta")
    _mk_response(student, school, EarlyOutreachResponseAction.INTERESTED)
    with as_path_admin():
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

    cards = client.get(RECAP_URL).json()["cards"]
    card = next(c for c in cards if c["kind"] == "school_response")
    assert "École insa-delta" in card["title"]
    assert "profil intéressant" in card["title"]
    assert card["stat_before"] == 45 and card["stat_after"] == 55  # AC1 avant/après
    assert card["cta_label"] == "Voir le parcours mis à jour"
    assert card["cta_url"].startswith("/mes-envois/")


@pytest.mark.django_db
def test_not_aligned_card_is_constructive_and_reroutes(client, student):
    _age_cursor(student, days=30)
    _mk_response(student, _mk_school("non-aligne"), EarlyOutreachResponseAction.NOT_ALIGNED)

    cards = client.get(RECAP_URL).json()["cards"]
    card = next(c for c in cards if c["kind"] == "school_response")
    # 8.4's diplomatic lexicon, NOT the epic's literal « a refusé » example
    # (deviation recorded in the story doc §2).
    assert "non aligné aujourd'hui" in card["title"]
    assert "pas un verdict" in card["body"]
    assert card["cta_label"] == "Explorer d'autres écoles"
    assert card["cta_url"] == "/schools"


@pytest.mark.django_db
def test_new_schools_card_counts_matches_only(client, student):
    _age_cursor(student, days=30)
    for i in range(2):
        school = _mk_school(f"nouvelle-delta-{i}")
        prof = Profession.objects.create(
            slug=f"metier-nd-{i}",
            name=f"Métier ND {i}",
            description="x" * 20,
            daily_routine="x" * 20,
            prospects_text="x",
            is_active=True,
            signals_json=MATCHING_SIGNALS,
        )
        Parcours.objects.create(
            profession=prof,
            target_school=school,
            niveau_scolaire="terminale_generale",
            label="Voie",
        )
    _mk_school("nouvelle-sans-parcours")  # no profession → no signal → not counted

    cards = client.get(RECAP_URL).json()["cards"]
    card = next(c for c in cards if c["kind"] == "new_schools")
    assert card["count"] == 2
    assert card["title"] == "2 nouvelles écoles correspondent à ton profil"
    assert card["cta_label"] == "Voir les nouvelles écoles"
    assert card["cta_url"] == "/schools"
    # Singular agreement on the 1-school variant: deactivate one of the two.
    School.objects.filter(slug="nouvelle-delta-1").update(is_active=False)
    single = next(
        c
        for c in compute_cards(student, timezone.now() - timedelta(days=30))
        if c["kind"] == "new_schools"
    )
    assert single["title"] == "1 nouvelle école correspond à ton profil"


@pytest.mark.django_db
def test_calendar_card_only_inside_its_window(client, student):
    _age_cursor(student, days=30)
    today = timezone.localdate()
    milestone = ParcoursupMilestone.objects.create(
        kind=MilestoneKind.OUVERTURE,
        campaign="2099-2100",
        date=today + timedelta(days=18),
        notify_days_before=30,
    )

    cards = client.get(RECAP_URL).json()["cards"]
    card = next(c for c in cards if c["kind"] == "parcoursup_milestone")
    assert card["days_until"] == 18
    assert len(card["recommended_actions"]) >= 3  # 8.7's non-blocking checklist
    assert card["cta_url"] in ("/mes-paris", "/profile")

    # Outside its own announcement window: not news yet.
    milestone.date = today + timedelta(days=60)
    milestone.save(update_fields=["date"])
    cards = client.get(RECAP_URL).json()["cards"]
    assert not any(c["kind"] == "parcoursup_milestone" for c in cards)


@pytest.mark.django_db
def test_stable_state_returns_empty_cards(client, student):
    _age_cursor(student, days=30)  # old cursor, but nothing moved
    assert client.get(RECAP_URL).json() == {"cards": []}


# ---------------------------------------------------------------------------
# Tone — every card the backend can produce, linted like 8.3/8.4/8.5
# ---------------------------------------------------------------------------

BANNED = [
    r"derni[eè]re chance",
    r"plus que \d+",
    r"\bvite\b",
    r"\burgent",
    r"!!",
    r"ne (rate|manque) pas",
    # 8.4's not-aligned markers — the negative delta must stay constructive.
    r"mauvaise nouvelle",
    r"malheureusement",
    r"\brefus",
    r"rejet",
    r"échec",
    # Anti-cirque (AC « pas confetti, pas 🎉 »).
    r"🎉",
    r"bravo !",
]


@pytest.mark.django_db(transaction=True)
def test_every_card_kind_passes_the_calm_tone_lint(student):
    _age_cursor(student, days=30)
    school = _mk_school("tone-check")
    for action in EarlyOutreachResponseAction:
        assert action in _RESPONSE_COPY  # a new action cannot ship without copy
    _mk_response(student, school, EarlyOutreachResponseAction.INTERESTED)
    prof = Profession.objects.create(
        slug="metier-tone",
        name="Métier Tone",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
        signals_json=MATCHING_SIGNALS,
    )
    Parcours.objects.create(
        profession=prof,
        target_school=school,
        niveau_scolaire="terminale_generale",
        label="Voie",
    )
    ParcoursupMilestone.objects.create(
        kind=MilestoneKind.RESULTATS_PRINCIPALE,
        campaign="2099-2100",
        date=timezone.localdate() + timedelta(days=5),
        notify_days_before=15,
    )

    cards = compute_cards(student, timezone.now() - timedelta(days=30))
    kinds = {c["kind"] for c in cards}
    assert kinds == {"school_response", "new_schools", "parcoursup_milestone"}

    # Lint the static copy table too — every action variant, not just the
    # one instantiated above.
    corpus = [str(v) for copy in _RESPONSE_COPY.values() for v in copy.values()]
    for card in cards:
        corpus.append(card["title"])
        corpus.append(card["body"])
        corpus.extend(card.get("recommended_actions") or [])
    rendered = "\n".join(corpus).lower()
    for pattern in BANNED:
        assert re.search(pattern, rendered) is None, f"banned marker {pattern!r}"
