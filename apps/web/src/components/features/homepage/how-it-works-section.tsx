/**
 * "Comment ça marche" section — Story 7.8 §AC2.
 *
 * Purely presentational; no data fetching. Uses an `<ol>` so the 4 steps
 * carry their sequential semantics for screen readers (RGAA AA).
 */
const STEPS = [
  {
    id: "profil",
    title: "1. Construis ton profil",
    description: "Passions, niveau scolaire, bulletins — Path-Advisor apprend à te connaître.",
  },
  {
    id: "recommandations",
    title: "2. Reçois des recommandations",
    description: "Des métiers qui te correspondent vraiment, expliqués et sourcés.",
  },
  {
    id: "parcours",
    title: "3. Explore ton parcours",
    description: "Formations, écoles, chances d'admission réelles pour chaque métier.",
  },
  {
    id: "suivi",
    title: "4. Suis ton évolution",
    description: "Ton profil et tes recommandations évoluent avec toi, année après année.",
  },
] as const;

export function HowItWorksSection() {
  return (
    <section aria-labelledby="how-it-works-heading" className="bg-bg-2 px-4 py-16">
      <h2
        id="how-it-works-heading"
        className="mb-10 text-center text-h2 font-semibold text-text md:text-h2-desktop"
      >
        Comment ça marche
      </h2>
      <ol className="mx-auto grid max-w-5xl list-none gap-6 md:grid-cols-4">
        {STEPS.map((step) => (
          <li
            key={step.id}
            className="flex flex-col gap-2 rounded-md border border-border bg-bg p-6"
          >
            <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">{step.title}</h3>
            <p className="text-body-sm text-text-muted">{step.description}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
