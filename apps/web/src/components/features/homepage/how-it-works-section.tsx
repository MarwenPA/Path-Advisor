import { useTranslations } from "next-intl";

/**
 * "Comment ça marche" section — Story 7.8 §AC2.
 *
 * Purely presentational; no data fetching. Uses an `<ol>` so the 4 steps
 * carry their sequential semantics for screen readers (RGAA AA).
 */
const STEP_IDS = ["profil", "recommandations", "parcours", "suivi"] as const;

export function HowItWorksSection() {
  const t = useTranslations("homepage.howItWorks");

  return (
    <section aria-labelledby="how-it-works-heading" className="bg-bg-2 px-4 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 max-w-2xl">
          <h2
            id="how-it-works-heading"
            className="text-h2 font-semibold text-text md:text-h2-desktop"
          >
            {t("title")}
          </h2>
          <p className="mt-2.5 text-body text-text-muted">{t("intro")}</p>
        </div>
        <ol className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-4">
          {STEP_IDS.map((id, index) => (
            <li
              key={id}
              className="grid content-start gap-2 rounded-lg border border-border bg-bg p-6"
            >
              <span
                className="text-caption font-semibold text-brand font-tabular"
                aria-hidden="true"
              >
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">
                {t(`steps.${id}.title`)}
              </h3>
              <p className="text-body-sm text-text-muted">{t(`steps.${id}.description`)}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
