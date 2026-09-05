/**
 * `/accueil` — student home dashboard, Story 8.8.
 *
 * Server Component composing 3 already-shipped bricks:
 *   1. "Ta progression" — `ProfileMaturityIndicator` variant="dashboard-card"
 *      (client, via `ProgressionModule` — TanStack Query owns its own
 *      loading/error state, see §4.2).
 *   2. "Tes métiers" — a single link to the full catalog (Story 3.13
 *      follow-up, 2026-09-05: dropped the score-card examples entirely per
 *      explicit request — "juste un bouton ... et pas d'exemple". No
 *      `fetchRecommendations()` call needed anymore for this module.
 *   3. "Tes paris" — top-3 `fetchMesParis()` as `FicheEcole` variant="card".
 *
 * `Promise.allSettled` (never `Promise.all`, see §4.4) fetches mes-paris in
 * parallel with anything else this page ever needs so one failing endpoint
 * never takes down another module.
 */
import Link from "next/link";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { FicheEcole } from "@/components/schools/FicheEcole";
import { fetchMesParis } from "@/lib/api/mes-paris";
import type { School } from "@/lib/api/schools";

import { ProgressionModule } from "./ProgressionModule";

export const metadata = { title: "Accueil — Path Advisor" };

const MAX_ITEMS = 3;

function topMesParis(schools: unknown): School[] {
  if (!Array.isArray(schools)) return [];
  return (schools as School[]).slice(0, MAX_ITEMS);
}

function MetiersModule() {
  return (
    <section aria-labelledby="accueil-metiers-title">
      <Card>
        <CardHeader>
          <h2 id="accueil-metiers-title" className="text-xl font-semibold text-foreground">
            Tes métiers
          </h2>
        </CardHeader>
        <CardContent>
          <Link
            href="/metiers"
            className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Voir la liste des métiers
          </Link>
        </CardContent>
      </Card>
    </section>
  );
}

function MesParisModule({ schools }: { schools: School[] }) {
  return (
    <section aria-labelledby="accueil-mesparis-title">
      <Card>
        <CardHeader>
          <h2 id="accueil-mesparis-title" className="text-xl font-semibold text-foreground">
            Tes paris
          </h2>
        </CardHeader>
        <CardContent>
          {schools.length === 0 ? (
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Tu n&apos;as pas encore exploré tes premiers paris. Va voir tes métiers recommandés
                et clique sur &laquo;&nbsp;Voir le parcours&nbsp;&raquo;.
              </p>
              <Link
                href="/mes-metiers"
                className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Voir mes métiers
              </Link>
            </div>
          ) : (
            <>
              <ul className="flex flex-col gap-4" data-testid="accueil-mesparis-list">
                {schools.map((s) => (
                  <li key={s.id}>
                    <FicheEcole school={s} variant="card" />
                  </li>
                ))}
              </ul>
              <Link
                href="/mes-paris"
                className="mt-4 inline-block text-sm text-primary hover:underline"
              >
                Voir tous mes paris
              </Link>
            </>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

export default async function AccueilPage() {
  // Promise.allSettled (never Promise.all, §4.4): a failing endpoint must
  // only degrade its own module, never take down the whole page.
  const [mesParisResult] = await Promise.allSettled([fetchMesParis()]);

  const schools = mesParisResult.status === "fulfilled" ? topMesParis(mesParisResult.value) : [];

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6">
      <h1 className="text-2xl font-bold">Accueil</h1>

      <ProgressionModule />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MetiersModule />
        <MesParisModule schools={schools} />
      </div>
    </main>
  );
}
