/**
 * /parametres/parrainage — Story 10.5 (FR-FF5) « Parrainer un pote ».
 * Lien traçable opaque + partage natif. Aucun incentive ni compteur
 * pressant (AC : pas de dark pattern, récompenses = V2).
 */
import type { Metadata } from "next";

import { ReferralPanel } from "./referral-panel";

export const metadata: Metadata = {
  title: "Parrainer un pote | Path-Advisor",
  description: "Partage ton lien Path-Advisor avec un pote.",
};

export default function ParrainagePage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">Parrainer un pote</h1>
        <p className="text-body text-text-muted">
          Partage ton lien : quand un·e pote s&apos;inscrit avec, tu le sauras. Rien de plus, rien
          de pressant.
        </p>
      </header>
      <ReferralPanel />
    </main>
  );
}
