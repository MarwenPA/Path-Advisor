"""School-side aggregate reporting — Story 5.10.

Only ever aggregates: no row here carries a student name or email (the
`User` model doesn't even have a name field) — RGPD-anonymous by
construction, not by a filtering step this module has to remember to
apply. The individual fiche (Story 5.6's `EcoleOutreachDetailView`) is the
only place an école sees anything about one specific student.

§2 scope decisions (deferred, documented rather than silently dropped):
    - "Répartition par région d'origine" — no such field exists anywhere
      on `User` (no address/lycée-region data collected in the MVP).
    - "Taux de conversion en candidature Parcoursup déclarée" — no
      Parcoursup-submission tracking exists anywhere in the codebase.
    - PDF export — the epic's AC says "CSV ou PDF"; CSV alone satisfies
      it, so no PDF-generation library was added for this story.
"""

from __future__ import annotations

import csv
import io
from datetime import date

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.outreach.models import EarlyOutreachRequest
from apps.schools.models import School


def build_school_reporting(*, school: School) -> dict:
    """AC — KPIs for the école's "Reporting" page.

    `by_action` includes a `"no_response"` bucket (yet-to-be-answered
    requests) alongside the 3 real `EarlyOutreachResponseAction` values,
    since "pas encore répondu" is itself a KPI a school cares about.
    """
    now = timezone.now()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    base = EarlyOutreachRequest.objects.filter(school=school)

    total_this_month = base.filter(created_at__gte=month_start).count()
    total_this_year = base.filter(created_at__gte=year_start).count()

    by_profession = list(
        base.values("profession__name")
        .annotate(count=Count("id"))
        .order_by("-count")
        .values("profession__name", "count")
    )

    by_month = list(
        base.filter(created_at__gte=year_start)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    responded = list(
        base.exclude(response__isnull=True)
        .values("response__action")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    no_response_count = base.filter(response__isnull=True).count()

    by_action = [{"action": row["response__action"], "count": row["count"]} for row in responded]
    if no_response_count:
        by_action.append({"action": "no_response", "count": no_response_count})

    return {
        "total_this_month": total_this_month,
        "total_this_year": total_this_year,
        "by_profession": [
            {"profession_name": row["profession__name"], "count": row["count"]}
            for row in by_profession
        ],
        "by_action": by_action,
        "by_month": [
            {
                "month": row["month"].isoformat()
                if isinstance(row["month"], date)
                else row["month"],
                "count": row["count"],
            }
            for row in by_month
        ],
    }


def export_school_reporting_csv(*, school: School) -> str:
    """AC — "je peux exporter le reporting en CSV ou PDF". One flat CSV
    with a section per breakdown (métier / mois / action) — good enough
    for a school admin to paste into their own spreadsheet; no PDF
    generation added (the AC's "ou" makes CSV alone sufficient)."""
    report = build_school_reporting(school=school)
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["Path-Advisor — reporting", school.name])
    writer.writerow([])
    writer.writerow(["Profils reçus ce mois", report["total_this_month"]])
    writer.writerow(["Profils reçus cette année", report["total_this_year"]])
    writer.writerow([])

    writer.writerow(["Répartition par métier visé"])
    writer.writerow(["Métier", "Nombre"])
    for row in report["by_profession"]:
        writer.writerow([row["profession_name"], row["count"]])
    writer.writerow([])

    writer.writerow(["Répartition par action"])
    writer.writerow(["Action", "Nombre"])
    for row in report["by_action"]:
        writer.writerow([row["action"], row["count"]])
    writer.writerow([])

    writer.writerow(["Répartition par mois (année en cours)"])
    writer.writerow(["Mois", "Nombre"])
    for row in report["by_month"]:
        writer.writerow([row["month"], row["count"]])

    return buffer.getvalue()
