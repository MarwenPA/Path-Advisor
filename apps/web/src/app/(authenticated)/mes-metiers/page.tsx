import { Suspense } from "react";

import { fetchRecommendations } from "@/lib/api/recommendations";

import { MetiersList } from "./MetiersList";
import MesMetiersLoading from "./loading";

export const metadata = { title: "Mes métiers — Path Advisor" };

export default async function MesMetiersPage() {
  const data = await fetchRecommendations();

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight text-gray-900">
        Mes métiers recommandés
      </h1>
      <Suspense fallback={<MesMetiersLoading />}>
        <MetiersList professions={data.results} />
      </Suspense>
    </main>
  );
}
