import { useTranslations } from "next-intl";

/**
 * "Comment ça marche" section — Story 7.8 §AC2.
 *
 * Purely presentational; no data fetching. Uses an `<ol>` so the 4 steps
 * carry their sequential semantics for screen readers (RGAA AA).
 *
 * Story 7.7 — strings moved to `messages/fr.json#homepage.howItWorks`.
 */
const STEP_IDS = ["profil", "recommandations", "parcours", "suivi"] as const;

export function HowItWorksSection() {
  const t = useTranslations("homepage.howItWorks");

  return (
    <section aria-labelledby="how-it-works-heading" className="bg-bg-2 px-4 py-16">
      <h2
        id="how-it-works-heading"
        className="mb-10 text-center text-h2 font-semibold text-text md:text-h2-desktop"
      >
        {t("title")}
      </h2>
      <ol className="mx-auto grid max-w-5xl list-none gap-6 md:grid-cols-4">
        {STEP_IDS.map((id) => (
          <li key={id} className="flex flex-col gap-2 rounded-md border border-border bg-bg p-6">
            <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">
              {t(`steps.${id}.title`)}
            </h3>
            <p className="text-body-sm text-text-muted">{t(`steps.${id}.description`)}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
