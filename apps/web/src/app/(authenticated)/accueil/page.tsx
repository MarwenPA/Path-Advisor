/**
 * `/accueil` — student home dashboard, Story 8.8.
 *
 * Layout restructured 2026-09-05 (explicit requests, in order):
 *   1. "l'accueil est pas terrible, Tes paris devrait être dans une
 *      section avec Ton profil, et Tes métiers/Tes écoles dans deux
 *      sections harmonieuses" → 2 rows: a "personal" card, then a
 *      2-column "explore the referential" row.
 *   2. "mets le bloc Tes paris dans Ta progression" → merged further:
 *      "Tes paris" is no longer its own sibling card, it's a subsection
 *      NESTED inside the single "Ta progression" card (one heading, one
 *      Card, "Tes paris" as an `<h3>` inside it). `ProgressionModule`
 *      itself now renders bare content only (no Card/section of its
 *      own) since this page owns the single wrapping card.
 *
 * Row 1 — `TaProgressionModule`: `ProgressionModule` content + a "Tes
 *   paris" subsection (favorited schools, `fetchMesParis()`), full width.
 * Row 2 — "explore the referential" pair, harmonised (same Card shape,
 *   same copy pattern — short description + single primary link, no data
 *   fetch needed): `MetiersModule` (→ `/metiers`) + `EcolesModule`
 *   (→ `/schools`), via the shared `<ExploreModule>`.
 *
 * `Promise.allSettled` (never `Promise.all`, see §4.4) fetches mes-paris in
 * parallel with anything else this page ever needs so one failing endpoint
 * never takes down another module.
 */
import Link from "next/link";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DeltaRecapInterstitial } from "@/components/delta-recap/DeltaRecapInterstitial";
import { FicheEcole } from "@/components/schools/FicheEcole";
import { fetchDeltaRecap } from "@/lib/api/delta-recap";
import { getTranslations } from "next-intl/server";

import { fetchMesParis } from "@/lib/api/mes-paris";
import type { School } from "@/lib/api/schools";

import { ProgressionModule } from "./ProgressionModule";

export const metadata = { title: "Accueil — Path Advisor" };

const MAX_ITEMS = 3;

/** Chrome strings live in fr.json#accueil (revue Epic 8 — 7.7 convention,
 * and fr.json is under the front tone lint). */
type Translator = Awaited<ReturnType<typeof getTranslations>>;

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

function MetiersModule({ t }: { t: Translator }) {
  return (
    <ExploreModule
      headingId="accueil-metiers-title"
      title={t("metiers.title")}
      description={t("metiers.description")}
      href="/metiers"
      linkLabel={t("metiers.linkLabel")}
    />
  );
}

function EcolesModule({ t }: { t: Translator }) {
  return (
    <ExploreModule
      headingId="accueil-ecoles-title"
      title={t("ecoles.title")}
      description={t("ecoles.description")}
      href="/schools"
      linkLabel={t("ecoles.linkLabel")}
    />
  );
}

/** "Ta progression" — now the single card for the whole "personal" row,
 * with "Tes paris" nested inside as a subsection (2026-09-05). */
function TaProgressionModule({ schools, t }: { schools: School[]; t: Translator }) {
  return (
    <section aria-labelledby="accueil-progression-title">
      <Card>
        <CardHeader>
          <h2 id="accueil-progression-title" className="text-xl font-semibold text-foreground">
            {t("progression.title")}
          </h2>
        </CardHeader>
        <CardContent className="space-y-6">
          <ProgressionModule />

          <div aria-labelledby="accueil-mesparis-title">
            <h3 id="accueil-mesparis-title" className="mb-3 text-lg font-semibold text-foreground">
              {t("mesParis.title")}
            </h3>
            {schools.length === 0 ? (
              <div className="space-y-4">
                <p className="text-muted-foreground">{t("mesParis.emptyBody")}</p>
                <Link
                  href="/mes-metiers"
                  className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                >
                  {t("mesParis.emptyCta")}
                </Link>
              </div>
            ) : (
              <>
                <ul className="flex flex-col gap-4" data-testid="accueil-mesparis-list">
                  {schools.map((s) => (
                    <li key={s.id}>
                      <FicheEcole school={s} variant="card" headingLevel="h4" />
                    </li>
                  ))}
                </ul>
                <Link
                  href="/mes-paris"
                  className="mt-4 inline-block text-sm text-primary hover:underline"
                >
                  {t("mesParis.seeAll")}
                </Link>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

export default async function AccueilPage() {
  const t = await getTranslations("accueil");
  // Promise.allSettled (never Promise.all, §4.4): a failing endpoint must
  // only degrade its own module, never take down the whole page. The
  // DeltaRecap fetch (Story 8.6) rides the same rule: if it fails, the
  // interstitial simply doesn't show — the home must never be hostage.
  const [mesParisResult, deltaRecapResult] = await Promise.allSettled([
    fetchMesParis(),
    fetchDeltaRecap(),
  ]);

  // allSettled degrades silently BY DESIGN, but never invisibly (revue
  // Epic 8, P2-9c): a recap endpoint failing for weeks would otherwise go
  // completely unnoticed — no interstitial, no signal.
  if (mesParisResult.status === "rejected") {
    console.error("[accueil] fetchMesParis failed", mesParisResult.reason);
  }
  if (deltaRecapResult.status === "rejected") {
    console.error("[accueil] fetchDeltaRecap failed", deltaRecapResult.reason);
  }

  const schools = mesParisResult.status === "fulfilled" ? topMesParis(mesParisResult.value) : [];
  // Array.isArray guard (revue Epic 8, P1-6): a malformed 200 ({}, null
  // cards) traverses allSettled — without the guard it crashed the whole
  // home at SSR time. Same class as the 8.8-review fix on topMesParis.
  const deltaCards =
    deltaRecapResult.status === "fulfilled" && Array.isArray(deltaRecapResult.value?.cards)
      ? deltaRecapResult.value.cards
      : [];

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6">
      {/* Story 8.6 — full-screen interstitial ABOVE the home when the
          student returns at J+1+ with deltas; renders nothing otherwise. */}
      <DeltaRecapInterstitial cards={deltaCards} />
      {/* tabIndex -1: the interstitial hands focus back here on close
          (revue Epic 8, P0-4 — focus restoration). */}
      <h1 id="accueil-title" tabIndex={-1} className="text-2xl font-bold outline-none">
        {t("title")}
      </h1>

      <TaProgressionModule schools={schools} t={t} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MetiersModule t={t} />
        <EcolesModule t={t} />
      </div>
    </main>
  );
}
