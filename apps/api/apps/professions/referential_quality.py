"""Story 10.3 — tableau de qualité du référentiel (FR-FF3).

Agrégats calculés à la demande pour `/admin/qualite` — le patron 9.6
(`ml_audit.build_audit_report`) : rien n'est stocké, le référentiel fait
quelques centaines de lignes, les buckets mensuels se font en Python.

Hébergé dans `professions` (l'app qui possède déjà l'outillage qualité :
signalements, révisions) bien qu'il agrège aussi `schools` et `outreach` —
consigné : un vrai foyer "referential" n'existe pas et deux imports
inter-apps ne justifient pas d'en créer un.

Fraîcheur : part des fiches PUBLIÉES dont la dernière édition date de moins
de 12 mois. « Dernière édition » = Max(revisions.created_at), repli sur
`created_at` pour les fiches seedées jamais éditées — plus strict que
`updated_at` (auto_now bouge sur n'importe quel save, y compris techniques).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Max
from django.utils import timezone

from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachRequestStatus,
    EarlyOutreachResponse,
)
from apps.schools.models import School, SchoolStatus

from .models import Profession, ProfessionReport, ProfessionStatus

#: Cibles produit (FR48) : MVP / growth.
PROFESSIONS_TARGETS = {"mvp": 50, "growth": 500}
SCHOOLS_TARGETS = {"mvp": 100, "growth": 1000}
#: Seuils d'alerte de l'AC.
OPEN_REPORTS_THRESHOLD = 20
FRESHNESS_THRESHOLD_PCT = 60.0
FRESHNESS_WINDOW_DAYS = 365
TREND_MONTHS = 6

_OPEN_REPORT_STATUSES = (ProfessionReport.Status.PENDING, ProfessionReport.Status.INFO_REQUESTED)


def _status_counts(model: type[Profession] | type[School], status_enum: Any) -> dict[str, int]:
    rows = dict(model.objects.values_list("status").annotate(n=Count("id")).order_by())
    return {value: rows.get(value, 0) for value in status_enum.values}


def _freshness_pct(model: type[Profession] | type[School]) -> float | None:
    """% de fiches publiées éditées dans la fenêtre. None sans fiche publiée
    (0 % serait un mensonge d'alerte sur un référentiel vide)."""
    cutoff = timezone.now() - timedelta(days=FRESHNESS_WINDOW_DAYS)
    rows = list(
        model.objects.filter(status="published")
        .annotate(last_edit=Max("revisions__created_at"))
        .values_list("last_edit", "created_at")
    )
    if not rows:
        return None
    fresh = sum(1 for last_edit, created_at in rows if (last_edit or created_at) >= cutoff)
    return round(100 * fresh / len(rows), 1)


def _month_key(dt: Any) -> str:
    return str(dt.strftime("%Y-%m"))


def _last_months(n: int = TREND_MONTHS) -> list[str]:
    now = timezone.now()
    months = []
    year, month = now.year, now.month
    for _ in range(n):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(months))


def _monthly_counts(qs: Any, field: str, months: list[str]) -> list[int]:
    since = timezone.now() - timedelta(days=31 * (len(months) + 1))
    buckets: dict[str, int] = dict.fromkeys(months, 0)
    for value in qs.filter(**{f"{field}__gte": since}).values_list(field, flat=True).iterator():
        key = _month_key(value)
        if key in buckets:
            buckets[key] += 1
    return [buckets[m] for m in months]


def build_quality_report() -> dict[str, Any]:
    """Le payload de `GET /api/v1/admin/referential-quality/`."""
    from apps.professions.models import ProfessionRevision
    from apps.schools.models import SchoolRevision

    professions = _status_counts(Profession, ProfessionStatus)
    schools = _status_counts(School, SchoolStatus)

    open_reports = ProfessionReport.objects.filter(status__in=_OPEN_REPORT_STATUSES).count()
    overdue_cutoff = timezone.now() - timedelta(days=7)
    overdue_reports = ProfessionReport.objects.filter(
        status__in=_OPEN_REPORT_STATUSES, created_at__lt=overdue_cutoff
    ).count()

    motivations_pending = EarlyOutreachRequest.objects.filter(
        status=EarlyOutreachRequestStatus.PENDING_MODERATION
    ).count()
    comments_pending = EarlyOutreachResponse.objects.filter(
        comment_status=EarlyOutreachResponse.CommentStatus.PENDING
    ).count()

    prof_freshness = _freshness_pct(Profession)
    school_freshness = _freshness_pct(School)

    months = _last_months()
    trends = {
        "months": months,
        "profession_edits": _monthly_counts(ProfessionRevision.objects.all(), "created_at", months),
        "school_edits": _monthly_counts(SchoolRevision.objects.all(), "created_at", months),
        "reports_opened": _monthly_counts(ProfessionReport.objects.all(), "created_at", months),
    }

    def freshness_alert(pct: float | None) -> bool:
        return pct is not None and pct < FRESHNESS_THRESHOLD_PCT

    return {
        "professions": {**professions, "targets": PROFESSIONS_TARGETS},
        "schools": {**schools, "targets": SCHOOLS_TARGETS},
        "freshness": {
            "window_days": FRESHNESS_WINDOW_DAYS,
            "threshold_pct": FRESHNESS_THRESHOLD_PCT,
            "professions_pct": prof_freshness,
            "schools_pct": school_freshness,
            "alert": freshness_alert(prof_freshness) or freshness_alert(school_freshness),
        },
        "reports": {
            "open": open_reports,
            "overdue": overdue_reports,
            "threshold": OPEN_REPORTS_THRESHOLD,
            "alert": open_reports > OPEN_REPORTS_THRESHOLD,
        },
        "moderation": {
            "motivations_pending": motivations_pending,
            "school_comments_pending": comments_pending,
        },
        "trends": trends,
    }
