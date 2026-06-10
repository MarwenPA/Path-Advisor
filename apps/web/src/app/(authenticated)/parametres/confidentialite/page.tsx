import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { ACCESS_LIST_COPY } from "@/lib/i18n/fr/access-list";

export const metadata: Metadata = {
  title: "Confidentialité | Path-Advisor",
  description:
    "Gère tes données personnelles, exerce ton droit à la portabilité RGPD et accède à l'historique des accès à ton profil.",
};

export default function ConfidentialitePage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">Confidentialité</h1>
        <p className="text-body text-text-muted">
          Tes données t&apos;appartiennent. Tu peux les récupérer à tout moment dans un format
          standard, ou demander leur suppression complète.
        </p>
      </header>

      <section className="flex flex-col gap-3 rounded-lg border border-border bg-bg p-6">
        <h2 className="text-h2 font-semibold text-text">Mes données personnelles</h2>
        <p className="text-body text-text-muted">
          Conformément à l&apos;Article 20 du RGPD (droit à la portabilité), tu peux télécharger
          l&apos;intégralité des données que Path-Advisor détient sur toi, dans un format structuré
          et machine-readable.
        </p>
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <Button asChild>
            <Link href="/parametres/confidentialite/mes-donnees">Gérer mes exports RGPD</Link>
          </Button>
          <p className="text-xs text-text-subtle">
            Tu peux lancer un export par 24 heures. L&apos;archive reste téléchargeable 7 jours
            après sa génération.
          </p>
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-lg border border-border bg-bg p-6">
        <h2 className="text-h2 font-semibold text-text">
          {ACCESS_LIST_COPY.parentSectionTitle}
        </h2>
        <p className="text-body text-text-muted">
          {ACCESS_LIST_COPY.parentSectionDescription}
        </p>
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <Button asChild>
            <Link href="/parametres/confidentialite/acces-tiers">
              {ACCESS_LIST_COPY.parentSectionCta}
            </Link>
          </Button>
        </div>
      </section>

      <section className="rounded-lg border border-dashed border-border-strong bg-bg-2 p-6">
        <h2 className="text-h2 font-semibold text-text">Suppression de compte</h2>
        <p className="text-body text-text-muted">
          Le droit à l&apos;oubli RGPD sera disponible dans une prochaine étape (Story 1.12). En
          attendant, écris à{" "}
          <a className="text-brand underline" href="mailto:dpo@path-advisor.fr">
            dpo@path-advisor.fr
          </a>{" "}
          pour exercer ce droit.
        </p>
      </section>
    </main>
  );
}
