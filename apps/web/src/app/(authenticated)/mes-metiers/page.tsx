import { fetchRecommendations } from "@/lib/api/recommendations";

import { MetiersList } from "./MetiersList";

export const metadata = { title: "Mes métiers — Path Advisor" };

export default async function MesMetiersPage() {
  const data = await fetchRecommendations();

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight text-gray-900">
        Mes métiers recommandés
      </h1>
      <MetiersList professions={data.results} niveauAdapted={data.niveau_adapted} />
    </main>
  );
}
