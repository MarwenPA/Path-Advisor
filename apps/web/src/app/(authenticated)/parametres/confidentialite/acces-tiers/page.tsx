/**
 * /parametres/confidentialite/acces-tiers — Story 1.9 §AC4, §AC5.
 *
 * Async Server Component (Next.js 15) — fetches the access list server-side
 * so the empty / populated decision is made before any HTML hits the
 * browser (no skeleton flash, no React StrictMode double-audit risk).
 */
import type { Metadata } from "next";

import { AccessListEmptyState } from "@/components/features/privacy/access-list-empty-state";
import { TierAccessCard } from "@/components/features/privacy/tier-access-card";
import { fetchAccessList } from "@/lib/api/access-list";
import { ACCESS_LIST_COPY } from "@/lib/i18n/fr/access-list";

export const metadata: Metadata = {
  title: "Accès tiers | Path-Advisor",
  description: "Liste des personnes et institutions qui ont accès à ton profil Path-Advisor.",
};

// Server-only data fetch. Errors propagate up to the Next.js error boundary
// in `error.tsx` (added Q3 ; today an exception renders the default 500).
export default async function AccesTiersPage() {
  const { results } = await fetchAccessList();

  return (
    <main
      className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12"
      aria-labelledby="tier-access-list-title"
    >
      <header className="flex flex-col gap-2">
        <h1
          id="tier-access-list-title"
          className="text-h1 font-semibold text-text md:text-h1-desktop"
        >
          {ACCESS_LIST_COPY.pageTitle}
        </h1>
        <p className="text-body text-text-muted">{ACCESS_LIST_COPY.pageDescription}</p>
      </header>

      <section aria-live="polite" className="flex flex-col gap-4">
        {results.length === 0 ? (
          <AccessListEmptyState />
        ) : (
          results.map((entry) => <TierAccessCard key={entry.id} entry={entry} />)
        )}
      </section>
    </main>
  );
}
