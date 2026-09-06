"""Export reporting anonymisé cohorte (CSV) — Story 6.9.

Scope decisions:
- **CSV only** — same "CSV ou PDF" AC wording as Story 5.10, same
  resolution: a single deterministic format satisfies the AC without a
  duplicate PDF renderer for the exact same aggregate numbers.
- **Synchronous, not an async job** — a cohort tops out at a few hundred
  students; the aggregation this reuses (`get_cohort_dashboard`) already
  runs well under a second. No queue/worker exists in this codebase for
  this kind of short report generation elsewhere (Story 5.10 is
  synchronous too) — introducing one here would be new infra for a
  sub-second computation, not a scope match for "< 30 s".
- **k-anonymity threshold (≥5)** — any `top_metiers`/`distribution_filiere`
  row with `count < 5` is folded into an "Autres (<5)" bucket rather than
  shown individually, per the AC's anti-reidentification requirement.
- **No nominative data** — the export only ever reads the same aggregate
  dict `get_cohort_dashboard` already returns; `eleves`/`activite_recente`
  (per-student rows) are deliberately excluded from the CSV.
"""

from __future__ import annotations

import csv
import hashlib
import io

from apps.accounts.models import User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.establishments.services.cohort_dashboard import get_cohort_dashboard

K_ANONYMITY_THRESHOLD = 5


def _fold_small_categories(rows: list[dict], *, key: str) -> list[dict]:
    kept = [r for r in rows if r["count"] >= K_ANONYMITY_THRESHOLD]
    folded_count = sum(r["count"] for r in rows if r["count"] < K_ANONYMITY_THRESHOLD)
    if folded_count:
        kept.append({key: "Autres (<5)", "count": folded_count})
    return kept


def export_cohort_reporting_csv(*, counselor: User) -> bytes:
    dashboard = get_cohort_dashboard(counselor=counselor)

    top_metiers = _fold_small_categories(dashboard["top_metiers"], key="name")
    distribution_filiere = _fold_small_categories(dashboard["distribution_filiere"], key="filiere")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Reporting cohorte anonymisé"])
    writer.writerow([])
    writer.writerow(["KPI", "Valeur"])
    writer.writerow(["Nombre d'élèves", dashboard["kpis"]["nb_eleves"]])
    writer.writerow(["Taux de complétion profil (%)", dashboard["kpis"]["taux_completion_profil"]])
    writer.writerow(["Élèves en mode dégradé", dashboard["kpis"]["nb_eleves_mode_degrade"]])
    writer.writerow([])
    writer.writerow(["Métier", "Nombre d'élèves"])
    for row in top_metiers:
        writer.writerow([row["name"], row["count"]])
    writer.writerow([])
    writer.writerow(["Filière", "Nombre d'élèves"])
    for row in distribution_filiere:
        writer.writerow([row["filiere"], row["count"]])

    content = buffer.getvalue().encode("utf-8")
    content_hash = hashlib.sha256(content).hexdigest()

    record_audit(
        action="establishments.cohort_reporting_exported",
        result=AuditResult.SUCCESS,
        actor=counselor,
        subject_id=str(counselor.tenant_id),
        metadata={"content_hash": content_hash, "nb_eleves": dashboard["kpis"]["nb_eleves"]},
    )
    return content
