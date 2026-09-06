/**
 * `/mes-envois/[id]` — Story 5.9 AC (fiche détail).
 *
 * Shows the motivation the student sent + the school's response (text +
 * action) + the stat impact + a link to the school's fiche.
 */
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchOutreachRequestDetail } from "@/lib/api/outreach";

export const metadata = { title: "Détail de l'envoi — Path Advisor" };

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  pending_moderation: "Motivation en cours de relecture",
  rejected: "Motivation refusée",
  responded: "École a répondu",
  expired_7d: "Expiré",
};

const ACTION_LABELS: Record<string, string> = {
  interested: "Profil intéressant — candidature encouragée",
  not_aligned: "Profil non aligné",
  interview_requested: "Demande d'entretien",
};

export default async function MesEnvoisDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let outreach;
  try {
    outreach = await fetchOutreachRequestDetail(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
      return null;
    }
    throw err;
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <Link href="/mes-envois" className="text-body-sm text-primary hover:underline">
        ← Retour à mes envois
      </Link>

      <h1 className="mb-6 mt-3 text-2xl font-bold">{outreach.school_name}</h1>

      <div className="flex flex-col gap-4 rounded-lg border border-border bg-card p-6">
        <div>
          <p className="text-caption text-text-subtle">Métier visé</p>
          <p className="text-body text-text">{outreach.profession_name}</p>
        </div>
        <div>
          <p className="text-caption text-text-subtle">Statut</p>
          <p className="text-body text-text">{STATUS_LABELS[outreach.status] ?? outreach.status}</p>
        </div>
        {outreach.motivation_text ? (
          <div>
            <p className="text-caption text-text-subtle">Ta motivation</p>
            <p className="whitespace-pre-wrap text-body text-text">{outreach.motivation_text}</p>
          </div>
        ) : null}
        {outreach.rejection_reason ? (
          <div>
            <p className="text-caption text-text-subtle">Motif du refus</p>
            <p className="text-body text-text">{outreach.rejection_reason}</p>
          </div>
        ) : null}
        {outreach.response ? (
          <div>
            <p className="text-caption text-text-subtle">Réponse de l&apos;école</p>
            <p className="text-body text-text">
              {ACTION_LABELS[outreach.response.action] ?? outreach.response.action}
            </p>
            {outreach.response.comment ? (
              <p className="mt-1 text-body-sm text-text-muted">{outreach.response.comment}</p>
            ) : null}
            <p className="mt-2 text-body-sm font-medium text-text">
              Impact sur ta stat : {outreach.response.stat_delta >= 0 ? "+" : ""}
              {outreach.response.stat_delta} pts
            </p>
          </div>
        ) : null}
      </div>

      <Link
        href={`/schools/${outreach.school_slug}`}
        className="mt-4 inline-block text-body-sm text-primary hover:underline"
      >
        Voir la fiche de {outreach.school_name} →
      </Link>
    </main>
  );
}
