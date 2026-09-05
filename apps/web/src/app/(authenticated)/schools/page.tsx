/**
 * `/schools` — catalogue complet des établissements du référentiel.
 *
 * Mirrors `/metiers` (Story 3.13): repli quand `/accueil`'s "Tes paris" n'a
 * pas encore de favoris — l'élève/parent peut quand même parcourir tout le
 * référentiel (72 écoles seedées) plutôt que de ne voir que ses favoris.
 * Chaque carte renvoie vers la fiche détail existante `/schools/{slug}`
 * (Story 4.4, inchangée).
 *
 * Server Component — un seul fetch, pas de pagination client pour l'instant
 * (72 écoles tiennent dans une page ; `fetchSchools` prend un `page` en
 * prévision de la croissance du référentiel).
 */
import Link from "next/link";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { fetchSchools } from "@/lib/api/schools";

export const metadata = { title: "Tous les établissements — Path Advisor" };

export default async function SchoolsCataloguePage() {
  const { results: schools } = await fetchSchools();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold">Tous les établissements</h1>
      <p className="mb-6 text-body text-text-muted">
        {schools.length} établissements à explorer, en attendant tes paris personnalisés.
      </p>

      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {schools.map((s) => (
          <li key={s.id}>
            <Link href={`/schools/${s.slug}`} className="block h-full">
              <Card className="h-full transition-colors hover:border-brand">
                <CardHeader>
                  <h2 className="text-h3 font-semibold text-text">{s.name}</h2>
                  <span className="text-caption uppercase tracking-wide text-text-subtle">
                    {s.type} · {s.city}
                  </span>
                </CardHeader>
                <CardContent>
                  <p className="text-body-sm text-text-muted">
                    Sélectivité {s.selectivity_index}/5 — {s.region}
                  </p>
                </CardContent>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
