/**
 * /mes-paris — list of schools bookmarked as favorites by the authenticated user.
 *
 * Story 4.8: Server Component that fetches GET /api/v1/mes-paris/ and renders
 * each school as a FicheEcole card (variant="card"). Empty state shows a CTA
 * linking to /mes-metiers.
 *
 * FicheEcole variant="card" is used as an interim placeholder.
 * TODO(story-4-12): replace with <ParcoursCard> once Story 4.12 ships.
 */

import { apiFetch } from "@/lib/api/client";
import { FicheEcole } from "@/components/schools/FicheEcole";
import type { School } from "@/lib/api/schools";

export const metadata = { title: "Mes Paris — Path Advisor" };

export default async function MesParisPage() {
  let schools: School[] = [];
  try {
    schools = await apiFetch<School[]>("/api/v1/mes-paris/");
  } catch {
    schools = [];
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="mb-6 text-2xl font-bold">Mes Paris</h1>
      {schools.length === 0 ? (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Tu n&apos;as pas encore exploré tes premiers paris. Va voir tes métiers recommandés et
            clique sur &laquo;&nbsp;Voir le parcours&nbsp;&raquo;.
          </p>
          <a
            href="/mes-metiers"
            className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Voir mes métiers
          </a>
        </div>
      ) : (
        <ul className="space-y-4">
          {schools.map((s) => (
            <li key={s.id}>
              {/* TODO(story-4-12): replace with <ParcoursCard> */}
              <FicheEcole school={s} variant="card" />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
