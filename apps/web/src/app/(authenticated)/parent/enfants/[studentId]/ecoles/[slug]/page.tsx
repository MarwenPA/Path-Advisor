/**
 * /parent/enfants/[studentId]/ecoles/[slug] — dedicated parent-scoped école
 * detail (AC2, code review 2026-08).
 *
 * Server Component: fetches the detail (forwarding the session cookie). A 403
 * (parent not linked) or 404 (unknown école) redirects — the backend is the
 * authority. Deliberately does NOT show the child's personal AdmissionStat
 * probability (bulletin-adjacent computed figure) — only public referential
 * school/formation data, per the same boundary as the dashboard (AC2/AC3).
 */
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchChildEcoleDetail } from "@/lib/api/parent";
import { PARENT_COPY } from "@/lib/i18n/fr/parent";

export const dynamic = "force-dynamic";

function formatCost(min: number | null, max: number | null): string {
  if (min === null && max === null) return "—";
  if (min === max) return `${min} €`;
  return `${min ?? 0} – ${max ?? 0} €`;
}

export default async function ParentChildEcoleDetailPage({
  params,
}: {
  params: Promise<{ studentId: string; slug: string }>;
}) {
  const { studentId, slug } = await params;
  const COPY = PARENT_COPY.ecoleDetail;

  let ecole;
  try {
    ecole = await fetchChildEcoleDetail(studentId, slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 403) {
      redirect(`/auth/forbidden?from=/parent/enfants/${encodeURIComponent(studentId)}`);
    }
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8">
      <Link
        href={`/parent/enfants/${encodeURIComponent(studentId)}`}
        className="text-body-sm text-primary hover:underline"
      >
        ← {COPY.backLabel}
      </Link>

      <h1 className="mt-4 text-h1 font-bold text-text">{ecole.name}</h1>
      <p className="mt-1 text-body-sm text-text-muted">
        {ecole.city} — {ecole.region}
      </p>

      {ecole.description && <p className="mt-6 text-body text-text">{ecole.description}</p>}

      <p className="mt-6 text-body-sm text-text-subtle">
        {COPY.costLabel} :{" "}
        <span className="font-mono tabular-nums">
          {formatCost(ecole.tuition_min_eur, ecole.tuition_max_eur)}
        </span>
      </p>

      <section className="mt-6">
        <h2 className="mb-2 text-h3 font-semibold text-text">{COPY.formationsTitle}</h2>
        {ecole.formations.length === 0 ? (
          <p className="text-body text-text-muted">{COPY.formationsEmpty}</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {ecole.formations.map((f) => (
              <li key={f.name} className="rounded-lg border border-border bg-card p-3">
                <p className="text-body font-medium text-text">{f.name}</p>
                <p className="text-body-sm text-text-muted">{f.duration_years} an(s)</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
