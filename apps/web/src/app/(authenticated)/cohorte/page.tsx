/**
 * `/cohorte` — Story 6.6 (dashboard cohorte conseillère B2B).
 *
 * Dense desktop layout (AC: 1440×900 no-scroll target) — a 2-column grid
 * of KPI cards + sections, no per-cohort picker (the counselor's whole
 * establishment is aggregated — see `cohort_dashboard.py` scope decision).
 */
import { CohortDashboard } from "@/components/features/establishments/cohort-dashboard";
import { COHORT_REPORTING_EXPORT_URL, fetchCohortDashboard } from "@/lib/api/cohort-dashboard";

export const metadata = { title: "Dashboard cohorte — Path Advisor" };

export default async function CohortDashboardPage() {
  const dashboard = await fetchCohortDashboard();

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
      <CohortDashboard dashboard={dashboard} />
    </main>
  );
}
