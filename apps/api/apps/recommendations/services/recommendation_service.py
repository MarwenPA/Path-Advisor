"""Story 3.4 — compute_recommendations: build profile, call ai-service, return top-8."""

from __future__ import annotations

from typing import Any

from apps.professions.models import Profession
from apps.students.models import StudentProfile

from . import ai_client

_BULLETINS_ENRICHED = {"partial", "completed"}


def _compute_bulletin_summary(profile: StudentProfile) -> dict[str, Any] | None:
    """Return {average: float} computed from all BulletinManual.matieres, or None."""
    from apps.bulletins.models import BulletinManual

    bulletins = list(BulletinManual.objects.filter(student=profile))
    if not bulletins:
        return None

    notes: list[float] = []
    for b in bulletins:
        for m in b.matieres or []:
            try:
                note = m.get("note")
                if note is not None:
                    val = float(note)
                    if val > 0:
                        notes.append(val)
            except (TypeError, ValueError):
                pass

    if not notes:
        return None

    avg = sum(notes) / len(notes)
    return {"average": round(avg, 2), "appreciation_keywords": []}


def compute_recommendations(user: Any) -> list[dict[str, Any]]:
    """
    Fetch student profile, call ai-service scorer, return top-8 sorted by score desc.

    Graceful degradation: missing profile → empty profile dict sent to ai-service.
    Unknown occupation_ids returned by ai-service are silently skipped.
    """
    # --- profile ---
    profile = StudentProfile.objects.filter(user=user).select_related("level_profile").first()

    has_bulletins: bool = bool(profile and profile.bulletins_status in _BULLETINS_ENRICHED)

    bulletin_summary = _compute_bulletin_summary(profile) if has_bulletins and profile else None

    level_profile = getattr(profile, "level_profile", None) if profile else None

    profile_dict: dict[str, Any] = {
        "passions": list(profile.passions or []) if profile else [],
        "valeurs": list(profile.valeurs or []) if profile else [],
        "niveau": (level_profile.level or "").strip() if level_profile else "",
        "specialites": list(level_profile.specialites or []) if level_profile else [],
        "has_bulletins": has_bulletins,
        "bulletin_summary": bulletin_summary,
    }

    # --- professions ---
    professions = list(Profession.objects.filter(is_active=True))
    occupation_ids = [p.id for p in professions]
    professions_data = [
        {
            "occupation_id": p.id,
            "signals_json": p.signals_json or {},
            "level_compatibility": p.level_compatibility or [],
        }
        for p in professions
    ]

    # --- score ---
    response = ai_client.score_metiers(
        student_id=str(user.pk),
        profile=profile_dict,
        occupation_ids=occupation_ids,
        professions_data=professions_data,
    )

    # --- merge & sort ---
    profession_by_id: dict[str, Profession] = {p.id: p for p in professions}

    scored_occupations: list[dict] = response.get("scored_occupations", [])
    scored_occupations.sort(key=lambda x: x.get("score", 0), reverse=True)

    results: list[dict[str, Any]] = []
    for item in scored_occupations[:8]:
        occ_id = item.get("occupation_id")
        p = profession_by_id.get(occ_id)
        if p is None:
            continue
        results.append(
            {
                "id": p.id,
                "slug": p.slug,
                "name": p.name,
                "sector": p.sector,
                "score": item.get("score", 0),
                "confidence_level": item.get("confidence_level", "low"),
                "signals_contributifs": item.get("signals_contributifs", []),
                "phrase_recopiable": "",
            }
        )

    return results
