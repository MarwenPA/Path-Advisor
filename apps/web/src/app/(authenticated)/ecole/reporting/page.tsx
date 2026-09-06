/**
 * `/ecole/reporting` — Story 5.10 AC (KPIs).
 *
 * Aggregate-only KPIs (no student names — the data model has none anyway):
 * profils reçus (mois + année), répartition par métier visé, par action
 * prise, détail par mois. "Répartition par région d'origine" and "taux de
 * conversion Parcoursup" are explicitly deferred (§2 scope decision — no
 * such data exists anywhere in the codebase yet). Export = CSV only (the
 * epic's AC says "CSV ou PDF" — CSV alone satisfies it).
 */
import { ECOLE_REPORTING_EXPORT_URL, fetchEcoleReporting } from "@/lib/api/ecole-reporting";

export const metadata = { title: "Reporting — Path Advisor" };

const ACTION_LABELS: Record<string, string> = {
  interested: "Profil intéressant",
  not_aligned: "Profil non aligné",
  interview_requested: "Demande d'entretien",
  no_response: "Pas encore répondu",
};

export default async function EcoleReportingPage() {
  const report = await fetchEcoleReporting();

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Reporting</h1>
        <a
          href={ECOLE_REPORTING_EXPORT_URL}
          className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-card"
        >
          Exporter en CSV
        </a>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4">
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-caption text-text-subtle">Profils reçus ce mois</p>
          <p className="text-h2 font-bold text-text">{report.total_this_month}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-caption text-text-subtle">Profils reçus cette année</p>
          <p className="text-h2 font-bold text-text">{report.total_this_year}</p>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="mb-3 text-h3 font-semibold text-text">Répartition par métier visé</h2>
        {report.by_profession.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucun profil reçu pour l&apos;instant.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {report.by_profession.map((row) => (
              <li
                key={row.profession_name}
                className="flex justify-between border-b border-border py-1 text-body-sm"
              >
                <span>{row.profession_name}</span>
                <span className="font-medium">{row.count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-h3 font-semibold text-text">Répartition par action prise</h2>
        {report.by_action.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune donnée pour l&apos;instant.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {report.by_action.map((row) => (
              <li
                key={row.action}
                className="flex justify-between border-b border-border py-1 text-body-sm"
              >
                <span>{ACTION_LABELS[row.action] ?? row.action}</span>
                <span className="font-medium">{row.count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-h3 font-semibold text-text">Détail par mois (année en cours)</h2>
        {report.by_month.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune donnée pour l&apos;instant.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {report.by_month.map((row) => (
              <li
                key={row.month}
                className="flex justify-between border-b border-border py-1 text-body-sm"
              >
                <span>
                  {new Date(row.month).toLocaleDateString("fr-FR", {
                    month: "long",
                    year: "numeric",
                  })}
                </span>
                <span className="font-medium">{row.count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
