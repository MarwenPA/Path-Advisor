import { useTranslations } from "next-intl";

/**
 * "Aha moments" showcase — Story 7.8 §AC2.
 *
 * Highlights the two flagship product moments (Epic 3 — vocational
 * recommendation, Epic 4 — path graph + admission stats). Marketing copy
 * only; no live data (unauthenticated visitors have no profile to score).
 *
 * Story 7.7 — strings moved to `messages/fr.json#homepage.ahaMoments`.
 */
const MOMENT_IDS = ["recommandation", "parcours"] as const;

export function AhaMomentsSection() {
  const t = useTranslations("homepage.ahaMoments");

  return (
    <section aria-labelledby="aha-moments-heading" className="bg-bg px-4 py-16">
      <h2
        id="aha-moments-heading"
        className="mb-10 text-center text-h2 font-semibold text-text md:text-h2-desktop"
      >
        {t("title")}
      </h2>
      <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-2">
        {MOMENT_IDS.map((id) => (
          <div key={id} className="flex flex-col gap-3 rounded-md border border-border bg-bg-2 p-8">
            <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">
              {t(`${id}.title`)}
            </h3>
            <p className="text-body-sm text-text-muted">{t(`${id}.description`)}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
