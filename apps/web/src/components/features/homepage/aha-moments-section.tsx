/**
 * "Aha moments" showcase — Story 7.8 §AC2.
 *
 * Highlights the two flagship product moments (Epic 3 — vocational
 * recommendation, Epic 4 — path graph + admission stats). Marketing copy
 * only; no live data (unauthenticated visitors have no profile to score).
 */
const MOMENTS = [
  {
    id: "recommandation",
    title: "Découvre les métiers faits pour toi",
    description:
      "Notre moteur de recommandation croise tes passions, ton niveau et tes résultats pour te proposer des métiers pertinents — avec les signaux expliqués en clair, jamais une boîte noire.",
  },
  {
    id: "parcours",
    title: "Vois tes vraies chances d'admission",
    description:
      "Pour chaque métier, un graphe de parcours te montre les formations possibles et une estimation personnalisée de tes chances d'admission dans chaque école.",
  },
] as const;

export function AhaMomentsSection() {
  return (
    <section aria-labelledby="aha-moments-heading" className="bg-bg px-4 py-16">
      <h2
        id="aha-moments-heading"
        className="mb-10 text-center text-h2 font-semibold text-text md:text-h2-desktop"
      >
        Ce qui change tout
      </h2>
      <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-2">
        {MOMENTS.map((moment) => (
          <div
            key={moment.id}
            className="flex flex-col gap-3 rounded-md border border-border bg-bg-2 p-8"
          >
            <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">{moment.title}</h3>
            <p className="text-body-sm text-text-muted">{moment.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
