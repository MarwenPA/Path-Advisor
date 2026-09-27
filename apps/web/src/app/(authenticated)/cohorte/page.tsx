/**
 * `/cohorte` — Story 6.6 (dashboard cohorte conseillère B2B).
 *
 * Dense desktop layout (AC: 1440×900 no-scroll target) — a 2-column grid
 * of KPI cards + sections, no per-cohort picker (the counselor's whole
 * establishment is aggregated — see `cohort_dashboard.py` scope decision).
 */
import { AtRiskPanel } from "@/components/features/establishments/at-risk-panel";
import { CohortDashboard } from "@/components/features/establishments/cohort-dashboard";
import {
  COHORT_REPORTING_EXPORT_URL,
  fetchAtRiskStudents,
  fetchCohortDashboard,
} from "@/lib/api/cohort-dashboard";

export const metadata = { title: "Dashboard cohorte — Path Advisor" };

export default async function CohortDashboardPage() {
  // Story 10.1 — les deux lectures sont indépendantes, en parallèle.
  const [dashboard, atRisk] = await Promise.all([fetchCohortDashboard(), fetchAtRiskStudents()]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Dashboard cohorte</h1>
        <a
          href={COHORT_REPORTING_EXPORT_URL}
          className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-card"
        >
          Exporter le reporting (CSV)
        </a>
      </div>
      {/* Story 10.1 — en tête : ce qui demande une action passe avant les stats. */}
      <AtRiskPanel initial={atRisk} />
      <CohortDashboard dashboard={dashboard} />
    </main>
  );
}
