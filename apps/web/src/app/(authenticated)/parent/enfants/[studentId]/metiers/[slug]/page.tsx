/**
 * /parent/enfants/[studentId]/metiers/[slug] — dedicated parent-scoped métier
 * detail (AC2, code review 2026-08).
 *
 * Server Component: fetches the detail (forwarding the session cookie). A 403
 * (parent not linked) or 404 (unknown métier) redirects — the backend is the
 * authority. No bulletin field is ever returned by the endpoint (AC2/AC3).
 */
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchChildMetierDetail } from "@/lib/api/parent";
import { PARENT_COPY } from "@/lib/i18n/fr/parent";

export const dynamic = "force-dynamic";

export default async function ParentChildMetierDetailPage({
  params,
}: {
  params: Promise<{ studentId: string; slug: string }>;
}) {
  const { studentId, slug } = await params;
  const COPY = PARENT_COPY.metierDetail;

  let metier;
  try {
    metier = await fetchChildMetierDetail(studentId, slug);
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

      <h1 className="mt-4 text-h1 font-bold text-text">{metier.name}</h1>
      {metier.sector && <p className="mt-1 text-body-sm text-text-muted">{metier.sector}</p>}

      <p className="mt-6 text-body text-text">{metier.description}</p>

      <section className="mt-6">
        <h2 className="mb-2 text-h3 font-semibold text-text">{COPY.dailyRoutineTitle}</h2>
        <p className="text-body text-text-muted">{metier.daily_routine}</p>
      </section>

      <section className="mt-6">
        <h2 className="mb-2 text-h3 font-semibold text-text">{COPY.prospectsTitle}</h2>
        <p className="text-body text-text-muted">{metier.prospects_text}</p>
      </section>

      <p className="mt-6 text-body-sm text-text-subtle">
        {COPY.salaryLabel} :{" "}
        <span className="font-mono tabular-nums">
          {metier.median_salary_eur !== null
            ? `${metier.median_salary_eur} € / an`
            : COPY.salaryUnknown}
        </span>
      </p>
    </main>
  );
}
