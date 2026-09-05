/**
 * `/accueil` — student home dashboard, Story 8.8.
 *
 * Layout restructured 2026-09-05 (explicit request — "l'accueil est pas
 * terrible, Tes paris devrait être dans une section avec Ton profil, et
 * Tes métiers/Tes écoles dans deux sections harmonieuses") into 2 rows:
 *   Row 1 — "personal" pair: `ProgressionModule` ("Ta progression") +
 *     `MesParisModule` (favorited schools, `fetchMesParis()`).
 *   Row 2 — "explore the referential" pair, harmonised (same Card shape,
 *     same copy pattern — short description + single primary link, no
 *     data fetch needed): `MetiersModule` (→ `/metiers`) + `EcolesModule`
 *     (→ `/schools`). The schools-catalog link used to live bolted onto
 *     "Tes paris" — split out into its own module for symmetry with
 *     "Tes métiers".
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

/** Shared shape for the two "explore the referential" cards (Row 2) — kept
 * as one component so `MetiersModule`/`EcolesModule` can never drift apart
 * visually (harmonized per explicit request). */
function ExploreModule({
  headingId,
  title,
  description,
  href,
  linkLabel,
}: {
  headingId: string;
  title: string;
  description: string;
  href: string;
  linkLabel: string;
}) {
  return (
    <section aria-labelledby={headingId} className="h-full">
      <Card className="flex h-full flex-col">
        <CardHeader>
          <h2 id={headingId} className="text-xl font-semibold text-foreground">
            {title}
          </h2>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col justify-between gap-4">
          <p className="text-muted-foreground">{description}</p>
          <Link
            href={href}
            className="inline-block w-fit rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            {linkLabel}
          </Link>
        </CardContent>
      </Card>
    </section>
  );
}

function MetiersModule() {
  return (
    <ExploreModule
      headingId="accueil-metiers-title"
      title="Tes métiers"
      description="Découvre tous les métiers du référentiel, avec description, quotidien type et perspectives d'évolution."
      href="/metiers"
      linkLabel="Voir la liste des métiers"
    />
  );
}

function EcolesModule() {
  return (
    <ExploreModule
      headingId="accueil-ecoles-title"
      title="Tes écoles"
      description="Explore tous les établissements du référentiel : type, ville, sélectivité."
      href="/schools"
      linkLabel="Voir la liste des établissements"
    />
  );
}

function MesParisModule({ schools }: { schools: School[] }) {
  return (
    <section aria-labelledby="accueil-mesparis-title" className="h-full">
      <Card className="flex h-full flex-col">
        <CardHeader>
          <h2 id="accueil-mesparis-title" className="text-xl font-semibold text-foreground">
            Tes paris
          </h2>
        </CardHeader>
        <CardContent className="flex-1">
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ProgressionModule />
        <MesParisModule schools={schools} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MetiersModule />
        <EcolesModule />
      </div>
    </main>
  );
}
