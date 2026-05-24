import type { Metadata } from "next";
import Link from "next/link";

import { GdprExportList } from "@/components/features/gdpr/gdpr-export-list";

export const metadata: Metadata = {
  title: "Mes données | Path-Advisor",
  description:
    "Demande un export RGPD complet de toutes les données personnelles que Path-Advisor détient sur toi, conformément à l'Article 20 du RGPD.",
};

export default function MesDonneesPage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <Link
          href="/parametres/confidentialite"
          className="text-sm text-text-muted hover:text-text"
        >
          ← Retour à Confidentialité
        </Link>
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          Mes données personnelles
        </h1>
        <p className="text-body text-text-muted">
          Exerce ton droit à la portabilité RGPD. L&apos;archive contient ton
          profil, l&apos;historique des accès à tes données, et toutes les
          autres données que Path-Advisor détient sur toi.
        </p>
      </header>

      <GdprExportList />

      <aside className="rounded-lg border border-border bg-bg-2 p-4 text-sm text-text-muted">
        <h2 className="text-h3 font-semibold text-text">Quelques précisions</h2>
        <ul className="mt-2 list-inside list-disc space-y-1">
          <li>
            L&apos;archive est chiffrée en AES-256 ; tu reçois le mot de passe
            dans un email <strong>séparé</strong> du lien.
          </li>
          <li>
            Pour ouvrir l&apos;archive : 7-Zip (Windows), Keka (Mac), p7zip
            (Linux). Le ZIP natif Windows ne sait pas lire l&apos;AES-256.
          </li>
          <li>
            Le lien est valable 7 jours, et tu peux télécharger l&apos;archive
            jusqu&apos;à 10 fois.
          </li>
          <li>
            Si tu perds le mot de passe, nous ne pouvons pas te le redonner —
            relance un nouvel export pour en obtenir un autre.
          </li>
        </ul>
      </aside>
    </main>
  );
}
