/**
 * `/ecole/outreach/[id]` — Story 5.6 (fiche détail) + Story 5.7 (réponse)
 * + Story 5.12 (`<EcoleResponseFlow>` generic component).
 *
 * Shows the synthetic profile a school is allowed to see for one request:
 * age, métier visé, parcours envisagé, motivation — explicitly NOT the
 * student's other recommendations or other targeted schools (NFR-S4),
 * which the backend never even sends (§2 scope decision, Story 5.4). The
 * page itself is now a thin data-fetching shell around
 * `<EcoleResponseFlow>`, which owns the header/sections/2-col layout +
 * the 3-action footer (or read-only response summary once answered).
 */
import Link from "next/link";
import { notFound } from "next/navigation";

import { EcoleResponseFlow } from "@/components/features/outreach/ecole-response-flow";
import { ApiError } from "@/lib/api/client";
import { fetchEcoleOutreachDetail } from "@/lib/api/ecole-outreach";

export const metadata = { title: "Profil reçu — Path Advisor" };

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
    <main className="mx-auto max-w-4xl px-4 py-8">
      <Link href="/ecole/outreach" className="text-body-sm text-primary hover:underline">
        ← Retour aux profils reçus
      </Link>

      <h1 className="mb-6 mt-3 text-2xl font-bold">Profil scolaire synthétique</h1>

      <EcoleResponseFlow outreach={outreach} />
    </main>
  );
}
