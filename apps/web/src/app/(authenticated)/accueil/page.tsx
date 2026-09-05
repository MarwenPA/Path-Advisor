/**
 * `/accueil` — student home dashboard, Story 8.8.
 *
 * Server Component composing 3 already-shipped bricks:
 *   1. "Ta progression" — `ProfileMaturityIndicator` variant="dashboard-card"
 *      (client, via `ProgressionModule` — TanStack Query owns its own
 *      loading/error state, see §4.2).
 *   2. "Tes métiers" — top-3 `fetchRecommendations().results` as
 *      `ScoreVocationnel` variant="compact" cards.
 *   3. "Tes paris" — top-3 `fetchMesParis()` as `FicheEcole` variant="card".
 *
 * `Promise.allSettled` (never `Promise.all`, see §4.4) fetches recommendations
 * and mes-paris in parallel so one failing endpoint never takes down the
 * other module — each renders its own empty state on failure instead.
 */
import Link from "next/link";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ScoreVocationnel } from "@/components/professions/ScoreVocationnel";
import type { Signal } from "@/components/professions/types";
import { FicheEcole } from "@/components/schools/FicheEcole";
import { fetchRecommendations, type ScoredProfession } from "@/lib/api/recommendations";
import { fetchMesParis } from "@/lib/api/mes-paris";
import type { School } from "@/lib/api/schools";

import { ProgressionModule } from "./ProgressionModule";

export const metadata = { title: "Accueil — Path Advisor" };

const MAX_ITEMS = 3;

/** Map ai-service confidence_level to ScoreVocationnel confidenceLevel prop. */
function mapConfidence(level: "low" | "medium" | "high"): "normal" | "indicative" {
  return level === "low" ? "indicative" : "normal";
}

/** Extract top-2 signal chips from signals_contributifs — same pattern as MetiersList. */
function toSignals(profession: ScoredProfession): Signal[] {
  return profession.signals_contributifs.slice(0, 2).map((s) => ({
    id: s.signal,
    label: s.signal.replace(/_/g, " "),
  }));
}

function topRecommendations(results: unknown): ScoredProfession[] {
  // Backend usage elsewhere assumes score-desc order; sort defensively rather
  // than trust it (§4.5 risk table).
  // Code-review fix (Story 8.8): a malformed 200 payload (missing/non-array
  // `results`) used to throw here — OUTSIDE the `allSettled` rejection path
  // — crashing the whole page and defeating the very isolation §4.4 exists
  // for. Guard defensively instead of trusting the response shape.
  if (!Array.isArray(results)) return [];
  return [...(results as ScoredProfession[])].sort((a, b) => b.score - a.score).slice(0, MAX_ITEMS);
}

function topMesParis(schools: unknown): School[] {
  if (!Array.isArray(schools)) return [];
  return (schools as School[]).slice(0, MAX_ITEMS);
}

function MetiersModule({ professions }: { professions: ScoredProfession[] }) {
  return (
    <section aria-labelledby="accueil-metiers-title">
      <Card>
        <CardHeader>
          <h2 id="accueil-metiers-title" className="text-xl font-semibold text-foreground">
            Tes métiers
          </h2>
        </CardHeader>
        <CardContent>
          {professions.length === 0 ? (
            <div className="space-y-4">
              <p className="text-body text-muted-foreground">
                Tes recommandations arrivent dès que ton profil est prêt.
              </p>
              {/* Story 3.13 — repli : en attendant un profil assez rempli pour
                  des recos scorées, l'élève peut quand même parcourir tout
                  le référentiel plutôt que de rester devant un module vide. */}
              <Link
                href="/metiers"
                className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Voir la liste des métiers
              </Link>
            </div>
          ) : (
            <>
              <ul className="flex flex-col gap-4" data-testid="accueil-metiers-list">
                {professions.map((p) => {
                  const encodedSignals = encodeURIComponent(JSON.stringify(p.signals_contributifs));
                  return (
                    <li key={p.id}>
                      <Link
                        href={`/metiers/${p.slug}?score=${p.score}&confidence=${p.confidence_level}&signals=${encodedSignals}`}
                        className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <ScoreVocationnel
                          metierId={p.id}
                          metiersName={p.name}
                          score={p.score}
                          phraseRecopiable={p.phrase_recopiable}
                          signals={toSignals(p)}
                          variant="compact"
                          confidenceLevel={mapConfidence(p.confidence_level)}
                        />
                      </Link>
                    </li>
                  );
                })}
              </ul>
              <Link
                href="/mes-metiers"
                className="mt-4 inline-block text-sm text-primary hover:underline"
              >
                Voir tous mes métiers
              </Link>
            </>
          )}
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
  const [recommendationsResult, mesParisResult] = await Promise.allSettled([
    fetchRecommendations(),
    fetchMesParis(),
  ]);

  const professions =
    recommendationsResult.status === "fulfilled"
      ? topRecommendations(recommendationsResult.value?.results)
      : [];
  const schools = mesParisResult.status === "fulfilled" ? topMesParis(mesParisResult.value) : [];

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6">
      <h1 className="text-2xl font-bold">Accueil</h1>

      <ProgressionModule />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MetiersModule professions={professions} />
        <MesParisModule schools={schools} />
      </div>
    </main>
  );
}
