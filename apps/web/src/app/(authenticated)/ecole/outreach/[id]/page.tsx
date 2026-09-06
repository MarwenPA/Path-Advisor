/**
 * `/ecole/outreach/[id]` — Story 5.6 (fiche détail).
 *
 * Shows the synthetic profile a school is allowed to see for one request:
 * age, métier visé, parcours envisagé, motivation — explicitly NOT the
 * student's other recommendations or other targeted schools (NFR-S4),
 * which the backend never even sends (§2 scope decision, Story 5.4).
 * No response actions here — those 3 buttons are Story 5.7.
 */
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchEcoleOutreachDetail } from "@/lib/api/ecole-outreach";

export const metadata = { title: "Profil reçu — Path Advisor" };

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  responded: "Répondu",
  expired_7d: "Expiré",
};

export default async function EcoleOutreachDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let outreach;
  try {
    outreach = await fetchEcoleOutreachDetail(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
      return null;
    }
    throw err;
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <Link href="/ecole/outreach" className="text-body-sm text-primary hover:underline">
        ← Retour aux profils reçus
      </Link>

      <h1 className="mb-6 mt-3 text-2xl font-bold">Profil scolaire synthétique</h1>

      <div className="flex flex-col gap-4 rounded-lg border border-border bg-card p-6">
        <div>
          <p className="text-caption text-text-subtle">Âge</p>
          <p className="text-body text-text">
            {outreach.student_age !== null ? `${outreach.student_age} ans` : "Non renseigné"}
          </p>
        </div>
        <div>
          <p className="text-caption text-text-subtle">Métier visé</p>
          <p className="text-body text-text">{outreach.profession_name}</p>
        </div>
        {outreach.parcours_label ? (
          <div>
            <p className="text-caption text-text-subtle">Parcours envisagé</p>
            <p className="text-body text-text">{outreach.parcours_label}</p>
          </div>
        ) : null}
        {outreach.motivation_text ? (
          <div>
            <p className="text-caption text-text-subtle">Motivation</p>
            <p className="whitespace-pre-wrap text-body text-text">{outreach.motivation_text}</p>
          </div>
        ) : null}
        <div>
          <p className="text-caption text-text-subtle">Statut</p>
          <p className="text-body text-text">{STATUS_LABELS[outreach.status] ?? outreach.status}</p>
        </div>
      </div>
    </main>
  );
}
