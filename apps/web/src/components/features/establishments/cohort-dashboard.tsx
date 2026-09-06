"use client";

/**
 * `<CohortDashboard>` — Story 6.6 (dashboard cohorte conseillère) AND
 * Story 6.10 (composant générique) in one: built generic from the start,
 * the same "later extraction story turns out already-done" pattern as
 * several Epic 5/6 stories this session — no chart library is installed
 * (confirmed via `package.json`), so histogram/pie are plain HTML/CSS bars,
 * consistent with the session's minimal-footprint precedent (Story 5.10's
 * CSV-only export).
 *
 * Keyboard shortcuts (dense desktop layout, AC): `/` focuses the student
 * search box, `j`/`k` move the selected row, `e` opens the selected
 * student's profile (Story 6.8). A full `⌘K` command palette is out of
 * scope for this pass — no command surface exists yet beyond this single
 * dashboard to make a palette meaningful; documented deferral, not a
 * silent drop.
 */
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import type { CohortDashboard as CohortDashboardData } from "@/lib/api/cohort-dashboard";

export function CohortDashboard({ dashboard }: { dashboard: CohortDashboardData }) {
  const router = useRouter();
  const searchRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);

  const filtered = useMemo(
    () =>
      dashboard.eleves.filter((e) =>
        `${e.student_id} ${e.cohort_name}`.toLowerCase().includes(query.toLowerCase()),
      ),
    [dashboard.eleves, query],
  );

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement;
      const isTyping = target.tagName === "INPUT" || target.tagName === "TEXTAREA";

      if (e.key === "/" && !isTyping) {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }
      if (isTyping) return;

      if (e.key === "j") {
        setSelected((s) => Math.min(s + 1, filtered.length - 1));
      } else if (e.key === "k") {
        setSelected((s) => Math.max(s - 1, 0));
      } else if (e.key === "e") {
        const eleve = filtered[selected];
        if (eleve) router.push(`/cohorte/eleves/${eleve.student_id}`);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [filtered, selected, router]);

  const maxMetier = Math.max(1, ...dashboard.top_metiers.map((m) => m.count));
  const maxFiliere = Math.max(1, ...dashboard.distribution_filiere.map((f) => f.count));
  const totalFiliere = dashboard.distribution_filiere.reduce((acc, f) => acc + f.count, 0) || 1;

  return (
    <div className="grid grid-cols-2 gap-4">
      <p className="col-span-2 rounded-lg border border-border bg-card p-3 text-body-sm text-text-subtle lg:hidden">
        Cette interface est optimisée pour desktop. Tu peux la consulter ici mais l&apos;efficacité
        y est sur grand écran.
      </p>

      <div className="col-span-2 grid grid-cols-3 gap-4">
        <div
          className="rounded-lg border border-border bg-card p-4"
          aria-label={`Élèves cohorte : ${dashboard.kpis.nb_eleves}`}
        >
          <p className="text-caption text-text-subtle">Élèves cohorte</p>
          <p className="text-h2 font-bold text-text">{dashboard.kpis.nb_eleves}</p>
        </div>
        <div
          className="rounded-lg border border-border bg-card p-4"
          aria-label={`Taux de complétion profil : ${dashboard.kpis.taux_completion_profil}%`}
        >
          <p className="text-caption text-text-subtle">Taux de complétion profil</p>
          <p className="text-h2 font-bold text-text">{dashboard.kpis.taux_completion_profil}%</p>
        </div>
        <div
          className="rounded-lg border border-border bg-card p-4"
          aria-label={`Élèves en mode dégradé : ${dashboard.kpis.nb_eleves_mode_degrade}`}
        >
          <p className="text-caption text-text-subtle">Élèves en mode dégradé</p>
          <p className="text-h2 font-bold text-text">{dashboard.kpis.nb_eleves_mode_degrade}</p>
        </div>
      </div>

      <section className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-h3 font-semibold text-text">Métiers les plus explorés</h2>
        {dashboard.top_metiers.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune donnée pour l&apos;instant.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {dashboard.top_metiers.map((m) => (
              <li key={m.name} className="text-body-sm">
                <div className="mb-1 flex justify-between">
                  <span>{m.name}</span>
                  <span className="font-medium">{m.count}</span>
                </div>
                <div
                  className="h-2 w-full rounded-full bg-muted"
                  role="img"
                  aria-label={`${m.name} : ${m.count} élève(s)`}
                >
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${(100 * m.count) / maxMetier}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-h3 font-semibold text-text">Distribution filière</h2>
        {dashboard.distribution_filiere.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune donnée pour l&apos;instant.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {dashboard.distribution_filiere.map((f) => (
              <li key={f.filiere} className="text-body-sm">
                <div className="mb-1 flex justify-between">
                  <span>{f.filiere}</span>
                  <span className="font-medium">
                    {f.count} ({Math.round((100 * f.count) / totalFiliere)}%)
                  </span>
                </div>
                <div
                  className="h-2 w-full rounded-full bg-muted"
                  role="img"
                  aria-label={`${f.filiere} : ${f.count} élève(s), ${Math.round((100 * f.count) / totalFiliere)}%`}
                >
                  <div
                    className="h-full rounded-full bg-secondary"
                    style={{ width: `${(100 * f.count) / maxFiliere}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="col-span-2 rounded-lg border border-border bg-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-h3 font-semibold text-text">Élèves</h2>
          <input
            ref={searchRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelected(0);
            }}
            placeholder="Rechercher un élève (/)"
            className="rounded-lg border border-border bg-background px-2 py-1 text-body-sm text-text"
          />
        </div>
        {filtered.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucun élève.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {filtered.map((eleve, i) => (
              <li
                key={eleve.student_id}
                className={`flex justify-between rounded px-2 py-1 text-body-sm ${
                  i === selected ? "bg-primary/10" : ""
                }`}
              >
                <a href={`/cohorte/eleves/${eleve.student_id}`} className="hover:underline">
                  {eleve.student_id}
                </a>
                <span className="text-text-subtle">{eleve.cohort_name}</span>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-caption text-text-subtle">
          Raccourcis : <kbd>/</kbd> rechercher · <kbd>j</kbd>/<kbd>k</kbd> naviguer · <kbd>e</kbd>{" "}
          ouvrir le profil (entretien)
        </p>
      </section>

      <section className="col-span-2 rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-h3 font-semibold text-text">Activité récente</h2>
        {dashboard.activite_recente.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune activité récente.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {dashboard.activite_recente.map((a) => (
              <li key={a.student_id} className="flex justify-between text-body-sm">
                <span>{a.student_id}</span>
                <span className="text-text-subtle">
                  {new Date(a.derniere_connexion).toLocaleString("fr-FR")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
