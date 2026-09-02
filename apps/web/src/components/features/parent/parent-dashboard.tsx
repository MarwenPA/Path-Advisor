"use client";

/**
 * ParentDashboard — Story 6.2 §T5.5 / AC1.
 *
 * Renders the three parent-visible sections for a linked child:
 *   1. Métiers explorés — compact `ScoreVocationnel` cards (reused, not rebuilt).
 *   2. Mes paris — the child's favorited schools.
 *   3. Coûts estimés — total + per-school breakdown.
 *
 * Receives already-fetched data from the Server Component page; contains no
 * fetch of its own. No bulletin data ever reaches this component (AC2/AC3).
 *
 * AC2 (code review, 2026-08): each card now links to a dedicated parent-scoped
 * detail view (`/parent/enfants/{studentId}/metiers|ecoles/{slug}`) — reusing
 * the student-facing `/metiers/[slug]` page was not an option, it's gated
 * `IsStudent`. Follows the same `<Link>`-wraps-`<ScoreVocationnel>` pattern as
 * `mes-metiers/MetiersList.tsx` — inner interactive elements (signal chips)
 * already `stopPropagation()` so they don't trigger navigation.
 */
import Link from "next/link";

import { ScoreVocationnel } from "@/components/professions/ScoreVocationnel";
import type { ParentChildDashboard } from "@/lib/api/parent";
import { PARENT_COPY } from "@/lib/i18n/fr/parent";

const COPY = PARENT_COPY.sections;

function formatCost(min: number | null, max: number | null): string {
  if ((min === null || min === 0) && (max === null || max === 0)) {
    return min === 0 && max === 0 ? COPY.costs.free : COPY.costs.unknown;
  }
  return COPY.costs.perYear(min ?? 0, max ?? 0);
}

export function ParentDashboard({
  dashboard,
  studentId,
}: {
  dashboard: ParentChildDashboard;
  studentId: string;
}) {
  const { metiers_explores, mes_paris, couts_estimes } = dashboard;
  const base = `/parent/enfants/${encodeURIComponent(studentId)}`;

  return (
    <div className="flex flex-col gap-8">
      {/* Section 1 — Métiers explorés */}
      <section aria-labelledby="parent-professions-title">
        <h2 id="parent-professions-title" className="mb-3 text-h2 font-semibold text-text">
          {COPY.professions.title}
        </h2>
        {metiers_explores.length === 0 ? (
          <p className="text-body text-text-muted">{COPY.professions.empty}</p>
        ) : (
          <div className="flex flex-wrap gap-4">
            {metiers_explores.map((m) => (
              <Link
                key={m.metier_id}
                href={`${base}/metiers/${encodeURIComponent(m.slug)}`}
                className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <ScoreVocationnel
                  metierId={m.metier_id}
                  metiersName={m.name}
                  score={m.score}
                  phraseRecopiable={m.phrase_recopiable}
                  signals={m.signals}
                  variant="compact"
                  confidenceLevel={m.confidence_level === "low" ? "indicative" : "normal"}
                />
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Section 2 — Mes paris */}
      <section aria-labelledby="parent-mesparis-title">
        <h2 id="parent-mesparis-title" className="mb-3 text-h2 font-semibold text-text">
          {COPY.mesParis.title}
        </h2>
        {mes_paris.length === 0 ? (
          <p className="text-body text-text-muted">{COPY.mesParis.empty}</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {mes_paris.map((p) => (
              <li key={p.school_id}>
                <Link
                  href={`${base}/ecoles/${encodeURIComponent(p.slug)}`}
                  className="flex items-center justify-between gap-2 rounded-lg border border-border bg-card p-4 hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <div>
                    <p className="text-body font-medium text-text">{p.name}</p>
                    <span className="text-body-sm text-text-muted">{p.city}</span>
                  </div>
                  <span className="text-body-sm text-text-subtle">
                    {formatCost(p.tuition_min_eur, p.tuition_max_eur)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Section 3 — Coûts estimés */}
      <section aria-labelledby="parent-costs-title">
        <h2 id="parent-costs-title" className="mb-3 text-h2 font-semibold text-text">
          {COPY.costs.title}
        </h2>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="mb-3 text-body font-medium text-text">
            {COPY.costs.total} :{" "}
            <span className="font-mono tabular-nums">
              {formatCost(couts_estimes.total_min_eur, couts_estimes.total_max_eur)}
            </span>
          </p>
          {couts_estimes.breakdown.length > 0 && (
            <ul className="flex flex-col gap-1.5">
              {couts_estimes.breakdown.map((b) => (
                <li
                  key={b.school_id}
                  className="flex items-center justify-between gap-2 text-body-sm"
                >
                  <span className="text-text-subtle">{b.school_name}</span>
                  <span className="font-mono tabular-nums text-text">
                    {formatCost(b.tuition_min_eur, b.tuition_max_eur)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <p className="text-caption text-text-muted">{PARENT_COPY.privacyNote}</p>
    </div>
  );
}
