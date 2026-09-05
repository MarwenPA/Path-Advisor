/**
 * `/metiers` — catalogue complet des métiers du référentiel. Story 3.13.
 *
 * Repli quand `/accueil`'s "Tes métiers" n'a pas encore de recommandations
 * scorées (profil pas assez rempli) — l'élève peut quand même parcourir
 * tout le référentiel (52 métiers seedés au lancement de cette story,
 * `apps/professions/management/commands/seed_professions.py`). Chaque
 * carte renvoie vers la fiche détail existante `/metiers/{slug}` (Story
 * 3.5/3.12, inchangée).
 *
 * Server Component — un seul fetch, pas de pagination client pour l'instant
 * (52 métiers tiennent dans une page ; `fetchProfessions` prend un `page`
 * en prévision de la croissance du référentiel, story de scraping future).
 */
import Link from "next/link";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { fetchProfessions } from "@/lib/api/professions";

export const metadata = { title: "Tous les métiers — Path Advisor" };

export default async function MetiersCataloguePage() {
  const { results: professions } = await fetchProfessions();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold">Tous les métiers</h1>
      <p className="mb-6 text-body text-text-muted">
        {professions.length} métiers à explorer, en attendant tes recommandations personnalisées.
      </p>

      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {professions.map((p) => (
          <li key={p.id}>
            <Link href={`/metiers/${p.slug}`} className="block h-full">
              <Card className="h-full transition-colors hover:border-brand">
                <CardHeader>
                  <h2 className="text-h3 font-semibold text-text">{p.name}</h2>
                  {p.sector && (
                    <span className="text-caption uppercase tracking-wide text-text-subtle">
                      {p.sector}
                    </span>
                  )}
                </CardHeader>
                <CardContent>
                  <p className="line-clamp-3 text-body-sm text-text-muted">{p.description}</p>
                  {p.median_salary_eur ? (
                    <p className="mt-2 text-body-sm font-medium text-text">
                      ~{p.median_salary_eur.toLocaleString("fr-FR")} € / an
                    </p>
                  ) : null}
                </CardContent>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
