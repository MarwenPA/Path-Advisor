/**
 * `/ecole/outreach` — Story 5.6 (reception queue).
 *
 * Server Component: lists the early-outreach requests sent to the
 * authenticated school admin's school, most recent first. Filter by
 * status via `?status=`; sort via `?ordering=`. No compatibility-score
 * column (§2 scope decision — no such score exists anywhere yet).
 * Responding to a request (Story 5.7) isn't built here — this is read-only
 * reception; each row links to the detail page.
 */
import Link from "next/link";

import { fetchEcoleOutreachQueue, type EcoleOutreachStatus } from "@/lib/api/ecole-outreach";

export const metadata = { title: "Profils reçus — Path Advisor" };

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  responded: "Répondu",
  expired_7d: "Expiré",
};

const STATUS_FILTERS: { value: EcoleOutreachStatus | ""; label: string }[] = [
  { value: "", label: "Tous" },
  { value: "pending", label: "En attente" },
  { value: "responded", label: "Répondu" },
  { value: "expired_7d", label: "Expiré" },
];

export default async function EcoleOutreachQueuePage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; ordering?: string }>;
}) {
  const params = await searchParams;
  const status =
    params.status === "pending" || params.status === "responded" || params.status === "expired_7d"
      ? params.status
      : undefined;
  const ordering = params.ordering === "created_at" ? "created_at" : "-created_at";

  const { results: requests } = await fetchEcoleOutreachQueue({ status, ordering });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold">Profils reçus</h1>
      <p className="mb-6 text-body-sm text-text-muted">
        Les envois anticipés d&apos;élèves visant ton établissement.
      </p>

      <nav className="mb-6 flex flex-wrap gap-2" aria-label="Filtrer par statut">
        {STATUS_FILTERS.map((f) => (
          <Link
            key={f.value}
            href={f.value ? `/ecole/outreach?status=${f.value}` : "/ecole/outreach"}
            className={`rounded-full border px-3 py-1 text-body-sm ${
              (status ?? "") === f.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-text-muted"
            }`}
          >
            {f.label}
          </Link>
        ))}
      </nav>

      {requests.length === 0 ? (
        <p className="text-body text-text-muted">Aucun profil reçu pour l&apos;instant.</p>
      ) : (
        <ul className="flex flex-col gap-4" data-testid="ecole-outreach-list">
          {requests.map((r) => (
            <li key={r.id} className="rounded-lg border border-border bg-card p-4">
              <Link href={`/ecole/outreach/${r.id}`} className="block">
                <p className="font-medium text-text">Métier visé : {r.profession_name}</p>
                {r.parcours_label ? (
                  <p className="text-body-sm text-text-muted">{r.parcours_label}</p>
                ) : null}
                <p className="text-caption text-text-subtle">
                  {r.student_age !== null ? `${r.student_age} ans — ` : ""}
                  {STATUS_LABELS[r.status] ?? r.status} —{" "}
                  {new Date(r.created_at).toLocaleDateString("fr-FR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
