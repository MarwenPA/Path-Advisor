"""Story 8.6 — the DeltaRecap cards: "voici ce qui a bougé" (UX-DR14/29).

ALL card copy is built HERE, server-side, so the calm-tone contract stays
executable in Python exactly like the 8.3/8.4/8.5 email lints — the front
renders strings, it never fabricates sentences. This is also the 8.7
groundwork: the calendar card already exposes `{days_until,
recommended_actions[]}` straight from `MILESTONE_COPY` (single copy source
shared with the 8.3 emails; only the rendering layer differs).

Card kinds and their AC mapping:
- `school_response`  — one card per `EarlyOutreachResponse` since the
  cursor, with the 5.8 before/after stat when it was applied. The
  `not_aligned` variant reuses the 8.4 DIPLOMATIC lexicon on purpose: the
  epic's own example says « a refusé », but `refus*` is a banned marker
  since 8.4 — constructive framing wins over the literal example
  (deviation recorded in the story doc §2).
- `new_schools`      — ONE aggregated card; relevance = the same local
  signal overlap as the 8.5 digest (`_signal_overlap`, `OVERLAP_MIN`),
  never an ai-service call.
- `parcoursup_milestone` — the next milestone inside its own
  `notify_days_before` window.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone
from django.utils.formats import date_format

from apps.outreach.models import EarlyOutreachResponse, EarlyOutreachResponseAction
from apps.schools.models import AdmissionStat, Parcours, School

from .milestone_copy import MILESTONE_COPY
from .models import DeltaRecapCursor, MilestoneKind, ParcoursupMilestone
from .tasks import OVERLAP_MIN, _signal_overlap

#: UX-DR29's "retour à J+1 ou plus" — younger cursors yield no recap.
RECAP_MIN_AGE = timedelta(hours=24)


def get_or_init_cursor(user) -> tuple[DeltaRecapCursor, bool]:
    """Return the user's cursor, creating the baseline at `now` if missing.

    A fresh account has no "since your last visit"; creating the baseline
    on first read is what makes a J+30 return computable at all (see the
    model docstring).
    """
    return DeltaRecapCursor.objects.get_or_create(user=user, defaults={"seen_at": timezone.now()})


def acknowledge(user) -> None:
    """Move the cursor to `now` — "Tout vu, continuer" or a card CTA click."""
    DeltaRecapCursor.objects.update_or_create(user=user, defaults={"seen_at": timezone.now()})


def compute_cards(user, since) -> list[dict[str, Any]]:
    """Everything that moved since `since`, as renderable cards."""
    cards: list[dict[str, Any]] = []
    cards.extend(_school_response_cards(user, since))
    new_schools = _new_schools_card(user, since)
    if new_schools is not None:
        cards.append(new_schools)
    milestone = _calendar_card()
    if milestone is not None:
        cards.append(milestone)
    return cards


# ---------------------------------------------------------------------------
# Réponse école (AC1 card 1) — with the 5.8 before/after stat
# ---------------------------------------------------------------------------

_RESPONSE_COPY = {
    EarlyOutreachResponseAction.INTERESTED: {
        "title": "{school} a répondu — profil intéressant",
        "body": (
            "Une réponse encourageante est arrivée pendant ton absence. "
            "Ton estimation d'admission pour cette école a été mise à jour."
        ),
        "cta_label": "Voir le parcours mis à jour",
    },
    EarlyOutreachResponseAction.NOT_ALIGNED: {
        "title": "{school} a répondu — profil non aligné aujourd'hui",
        "body": (
            "C'est une information utile, pas un verdict. D'autres écoles "
            "accueillent des profils proches du tien — ton estimation a été "
            "mise à jour pour t'aider à viser juste."
        ),
        "cta_label": "Explorer d'autres écoles",
    },
    EarlyOutreachResponseAction.INTERVIEW_REQUESTED: {
        "title": "{school} propose un entretien",
        "body": (
            "L'école souhaite échanger avec toi et propose des créneaux. "
            "Tu peux les consulter et répondre quand tu es prêt·e."
        ),
        "cta_label": "Voir le parcours mis à jour",
    },
}


def _school_response_cards(user, since) -> list[dict[str, Any]]:
    responses = list(
        EarlyOutreachResponse.objects.filter(request__student_id=user.pk, created_at__gte=since)
        .select_related("request__school")
        .order_by("-created_at")
    )
    if not responses:
        return []

    # 5.8's before/after lives on AdmissionStat (school, user). One query.
    school_ids = {r.request.school_id for r in responses}
    stats = {
        s.school_id: s
        for s in AdmissionStat.objects.filter(
            school_id__in=school_ids, user_id=user.pk, previous_proba__isnull=False
        )
    }

    cards: list[dict[str, Any]] = []
    for response in responses:
        school = response.request.school
        copy = _RESPONSE_COPY[EarlyOutreachResponseAction(response.action)]
        stat = stats.get(school.id)
        if response.action == EarlyOutreachResponseAction.NOT_ALIGNED:
            cta_url = "/schools"
        else:
            cta_url = f"/mes-envois/{response.request_id}"
        cards.append(
            {
                "kind": "school_response",
                "title": str(copy["title"]).format(school=school.name),
                "body": copy["body"],
                "cta_label": copy["cta_label"],
                "cta_url": cta_url,
                # AC1's « stat avant/après » — None when 5.8 never applied
                # a delta (e.g. propagation failed); front hides the chip.
                "stat_before": stat.previous_proba if stat else None,
                "stat_after": stat.expected_proba if stat else None,
            }
        )
    return cards


# ---------------------------------------------------------------------------
# Nouvelles écoles (AC1 card 2) — same relevance rule as the 8.5 digest
# ---------------------------------------------------------------------------


def _new_schools_card(user, since) -> dict[str, Any] | None:
    profile = getattr(user, "student_profile", None)
    if profile is None:
        return None  # non-student account (parent…) — no vocational signals
    level = getattr(profile, "level_profile", None)
    profile_signals = {
        "passions": profile.passions,
        "valeurs": profile.valeurs,
        "specialites": (level.specialites if level else []) or [],
    }

    new_schools = list(School.objects.filter(is_active=True, created_at__gte=since))
    if not new_schools:
        return None

    parcours = Parcours.objects.filter(
        target_school__in=new_schools, profession__is_active=True
    ).select_related("profession")
    school_professions: dict[str, list] = {}
    for p in parcours:
        school_professions.setdefault(str(p.target_school_id), []).append(p.profession)

    count = 0
    for school in new_schools:
        best = max(
            (
                _signal_overlap(profile_signals, prof.signals_json or {})
                for prof in school_professions.get(str(school.id), [])
            ),
            default=0,
        )
        if best >= OVERLAP_MIN:
            count += 1
    if count == 0:
        return None

    if count == 1:
        title = "1 nouvelle école correspond à ton profil"
    else:
        title = f"{count} nouvelles écoles correspondent à ton profil"
    return {
        "kind": "new_schools",
        "title": title,
        "body": (
            "Ajoutées depuis ta dernière visite, ces écoles mènent à des "
            "métiers proches de tes passions et de tes valeurs."
        ),
        "cta_label": "Voir les nouvelles écoles",
        "cta_url": "/schools",
        "count": count,
        "stat_before": None,
        "stat_after": None,
    }


# ---------------------------------------------------------------------------
# Calendrier Parcoursup (AC1 card 3) — MILESTONE_COPY, single source (8.7)
# ---------------------------------------------------------------------------


def _calendar_card() -> dict[str, Any] | None:
    today = timezone.localdate()
    upcoming = ParcoursupMilestone.objects.filter(date__gte=today).order_by("date").first()
    if upcoming is None:
        return None
    days_until = (upcoming.date - today).days
    if days_until > upcoming.notify_days_before:
        return None  # outside its own announcement window — not news yet

    copy = MILESTONE_COPY[MilestoneKind(upcoming.kind)]
    date_fr = date_format(upcoming.date, "j F Y")
    return {
        "kind": "parcoursup_milestone",
        "title": str(copy["subject"]).format(date=date_fr),
        "body": str(copy["intro"]).format(date=date_fr),
        "cta_label": copy["cta_label"],
        "cta_url": copy["cta_path"],
        "days_until": days_until,
        # 8.7's CalendarNotification shape: non-blocking suggestions.
        "recommended_actions": copy["checklist"],
        "stat_before": None,
        "stat_after": None,
    }
