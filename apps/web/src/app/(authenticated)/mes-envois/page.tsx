/**
 * `/mes-envois` — Story 5.4 §AC4 + Story 5.5 (moderation) + Story 5.7
 * (school response + interview follow-up) + Story 5.9 (grouped history).
 *
 * Grouped by status/action per the epic's 5 buckets: En attente / Réponses
 * positives / Réponses négatives / Entretiens demandés / Expirés.
 * `pending_moderation`/`rejected` (Story 5.5, added after the epic's
 * original 5-bucket AC was written) fold into "En attente" — they're
 * sub-states of "not yet responded", not a 6th bucket.
 */
import Link from "next/link";

import { InterviewResponseForm } from "@/components/features/outreach/interview-response-form";
import { ResubmitMotivationForm } from "@/components/features/outreach/resubmit-motivation-form";
import { fetchOutreachRequests, type EarlyOutreachRequestItem } from "@/lib/api/outreach";

export const metadata = { title: "Mes envois — Path Advisor" };

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  pending_moderation: "Motivation en cours de relecture",
  rejected: "Motivation refusée",
  responded: "École a répondu",
  expired_7d: "Expiré",
};

type Bucket = "en_attente" | "positives" | "negatives" | "entretiens" | "expires";

const BUCKET_TITLES: Record<Bucket, string> = {
  en_attente: "En attente",
  positives: "Réponses positives",
  negatives: "Réponses négatives",
  entretiens: "Entretiens demandés",
  expires: "Expirés",
};

function bucketOf(r: EarlyOutreachRequestItem): Bucket {
  if (r.status === "expired_7d") return "expires";
  if (r.status === "responded" && r.response) {
    if (r.response.action === "interested") return "positives";
    if (r.response.action === "not_aligned") return "negatives";
    if (r.response.action === "interview_requested") return "entretiens";
  }
  return "en_attente";
}

function StatDeltaBadge({ delta }: { delta: number }) {
  const sign = delta >= 0 ? "+" : "";
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-caption font-semibold ${
        delta >= 0 ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
      }`}
    >
      {sign}
      {delta} pts
    </span>
  );
}

function OutreachCard({ r }: { r: EarlyOutreachRequestItem }) {
  return (
    <li className="rounded-lg border border-border bg-card p-4">
      <Link href={`/mes-envois/${r.id}`} className="block">
        <div className="flex items-center justify-between gap-2">
          <p className="font-medium text-text">{r.school_name}</p>
          {r.response ? <StatDeltaBadge delta={r.response.stat_delta} /> : null}
        </div>
        <p className="text-body-sm text-text-muted">Métier visé : {r.profession_name}</p>
        <p className="text-caption text-text-subtle">
          {STATUS_LABELS[r.status] ?? r.status} —{" "}
          {new Date(r.created_at).toLocaleDateString("fr-FR", {
            day: "numeric",
            month: "long",
            year: "numeric",
          })}
        </p>
      </Link>
      {r.status === "rejected" ? (
        <ResubmitMotivationForm outreachId={r.id} rejectionReason={r.rejection_reason} />
      ) : null}
      {r.response?.action === "interview_requested" &&
      !r.response.accepted_slot &&
      !r.response.alternative_note ? (
        <InterviewResponseForm outreachId={r.id} proposedSlots={r.response.proposed_slots} />
      ) : null}
      {r.response?.accepted_slot ? (
        <p className="mt-2 text-body-sm text-text-muted">
          Créneau accepté : {new Date(r.response.accepted_slot).toLocaleString("fr-FR")}
        </p>
      ) : null}
      {r.response?.alternative_note ? (
        <p className="mt-2 text-body-sm text-text-muted">
          Ta proposition : {r.response.alternative_note}
        </p>
      ) : null}
    </li>
  );
}

export default async function MesEnvoisPage() {
  const { results: requests } = await fetchOutreachRequests();

  const groups: Record<Bucket, EarlyOutreachRequestItem[]> = {
    en_attente: [],
    positives: [],
    negatives: [],
    entretiens: [],
    expires: [],
  };
  for (const r of requests) {
    groups[bucketOf(r)].push(r);
  }

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
        <div className="flex flex-col gap-8" data-testid="mes-envois-list">
          {(Object.keys(BUCKET_TITLES) as Bucket[]).map((bucket) =>
            groups[bucket].length === 0 ? null : (
              <section key={bucket}>
                <h2 className="mb-3 text-h3 font-semibold text-text">
                  {BUCKET_TITLES[bucket]} ({groups[bucket].length})
                </h2>
                <ul className="flex flex-col gap-4">
                  {groups[bucket].map((r) => (
                    <OutreachCard key={r.id} r={r} />
                  ))}
                </ul>
              </section>
            ),
          )}
        </div>
      )}
    </main>
  );
}
