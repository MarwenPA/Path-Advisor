import { useTranslations } from "next-intl";

// Fictional profile shown to anonymous visitors (they have no data to score);
// the bar widths are illustrative only.
const SIGNALS = [
  { id: "interest", width: 88 },
  { id: "grades", width: 74 },
  { id: "comments", width: 66 },
] as const;

export function RecommendationExample() {
  const t = useTranslations("homepage.hero.example");

  return (
    <aside
      aria-label={t("ariaLabel")}
      className="grid gap-3.5 rounded-lg border border-border bg-bg-2 p-5"
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-caption font-semibold uppercase tracking-[0.06em] text-text-subtle">
          {t("label")}
        </span>
        <span className="text-h3 font-semibold text-brand font-tabular">{t("score")}</span>
      </div>
      <div>
        <p className="text-h3 font-semibold text-text md:text-h3-desktop">{t("job")}</p>
        <p className="text-body-sm text-text-muted">{t("jobMeta")}</p>
      </div>
      <ul aria-label={t("signalsLabel")} className="grid gap-2">
        {SIGNALS.map((signal) => (
          <li
            key={signal.id}
            className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-2 text-body-sm"
          >
            <span className="text-text">{t(`signals.${signal.id}.label`)}</span>
            <span className="text-text-subtle font-tabular">{t(`signals.${signal.id}.value`)}</span>
            <span
              className="col-span-2 h-1.5 overflow-hidden rounded-full bg-bg-3"
              aria-hidden="true"
            >
              <span
                className="block h-full rounded-full bg-brand"
                style={{ width: `${signal.width}%` }}
              />
            </span>
          </li>
        ))}
      </ul>
      <p className="border-t border-dashed border-border-strong pt-3 text-body-sm text-text-muted">
        <strong className="font-semibold text-text">{t("whyTitle")}</strong> {t("whyText")}
      </p>
    </aside>
  );
}
