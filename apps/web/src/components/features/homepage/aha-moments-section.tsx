import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { ParcoursExampleGraph } from "./parcours-example-graph";

/**
 * "Aha moments" showcase — Story 7.8 §AC2.
 *
 * Highlights the two flagship product moments (Epic 3 — vocational
 * recommendation, Epic 4 — path graph + admission stats). Marketing copy
 * only; no live data (unauthenticated visitors have no profile to score).
 */
const EXAMPLE_IDS = ["biomedical", "orthoptiste", "dataSante", "kine"] as const;

const LEGEND = [
  { id: "sur", dot: "bg-semantic-sur" },
  { id: "realiste", dot: "bg-semantic-realiste" },
  { id: "audacieux", dot: "bg-semantic-audacieux" },
] as const;

export function AhaMomentsSection() {
  const t = useTranslations("homepage.ahaMoments");

  return (
    <section aria-labelledby="aha-moments-heading" className="bg-bg px-4 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 max-w-2xl">
          <h2
            id="aha-moments-heading"
            className="text-h2 font-semibold text-text md:text-h2-desktop"
          >
            {t("title")}
          </h2>
          <p className="mt-2.5 text-body text-text-muted">{t("intro")}</p>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <article className="grid content-start gap-4 rounded-lg border border-border bg-bg-2 p-8">
            <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">
              {t("recommandation.title")}
            </h3>
            <p className="text-body-sm text-text-muted">{t("recommandation.description")}</p>
            <ul aria-label={t("recommandation.examplesLabel")} className="flex flex-wrap gap-2">
              {EXAMPLE_IDS.map((id) => (
                <li key={id}>
                  <Badge variant="outline" className="bg-bg font-medium text-text font-tabular">
                    {t(`recommandation.examples.${id}`)}
                  </Badge>
                </li>
              ))}
            </ul>
          </article>

          <article className="grid content-start gap-4 rounded-lg border border-border bg-bg-2 p-8">
            <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">
              {t("parcours.title")}
            </h3>
            <p className="text-body-sm text-text-muted">{t("parcours.description")}</p>
            <ul aria-label={t("parcours.legendLabel")} className="flex flex-wrap gap-2">
              {LEGEND.map((item) => (
                <li key={item.id}>
                  <Badge variant="outline" className="gap-1.5 bg-bg font-medium text-text">
                    <span className={cn("size-2 rounded-full", item.dot)} aria-hidden="true" />
                    {t(`parcours.legend.${item.id}`)}
                  </Badge>
                </li>
              ))}
            </ul>
            <ParcoursExampleGraph />
          </article>
        </div>
      </div>
    </section>
  );
}
