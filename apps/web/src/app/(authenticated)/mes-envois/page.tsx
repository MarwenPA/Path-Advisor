/**
 * `/mes-envois` — Story 5.4 §AC4.
 *
 * Minimal flat list (école, métier visé, date, statut) — Story 5.9 will
 * enrich this with grouping by status, a detail view, and the stat-impact
 * badge. Every request is `pending` today (no école-side response flow
 * exists yet, Story 5.6/5.7), so the status column is a placeholder for now.
 */
import Link from "next/link";

import { fetchOutreachRequests } from "@/lib/api/outreach";

export const metadata = { title: "Mes envois — Path Advisor" };

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  responded: "École a répondu",
  expired_7d: "Expiré",
};

export default async function MesEnvoisPage() {
  const { results: requests } = await fetchOutreachRequests();

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">Mes envois</h1>

      {requests.length === 0 ? (
        <div className="space-y-4">
          <p className="text-body text-text-muted">
            Tu n&apos;as pas encore envoyé ton profil à une école. C&apos;est une feature premium
            qui peut booster tes chances d&apos;admission.
          </p>
          <Link
            href="/schools"
            className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Voir les écoles partenaires
          </Link>
        </div>
      ) : (
        <ul className="flex flex-col gap-4" data-testid="mes-envois-list">
          {requests.map((r) => (
            <li key={r.id} className="rounded-lg border border-border bg-card p-4">
              <p className="font-medium text-text">{r.school_name}</p>
              <p className="text-body-sm text-text-muted">Métier visé : {r.profession_name}</p>
              <p className="text-caption text-text-subtle">
                {STATUS_LABELS[r.status] ?? r.status} —{" "}
                {new Date(r.created_at).toLocaleDateString("fr-FR", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
