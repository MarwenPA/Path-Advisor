"use client";

import { useTranslations } from "next-intl";

import type { School, Formation } from "@/lib/api/schools";
import { cn } from "@/lib/utils";
import { AdmissionStatPoller } from "./AdmissionStatPoller";

interface FicheEcoleProps {
  school: School;
  variant?: "card" | "expanded" | "compare";
  className?: string;
  isSelected?: boolean;
  onSelect?: (schoolId: string) => void;
}

function SelectivityStars({ index }: { index: number }) {
  const t = useTranslations("ficheEcole");
  return (
    <div aria-label={t("selectivityAria", { index })} className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={cn("text-sm", i <= index ? "text-amber-500" : "text-gray-200")}>
          ★
        </span>
      ))}
    </div>
  );
}

function FormationItem({ formation }: { formation: Formation }) {
  const t = useTranslations("ficheEcole");
  return (
    <li className="flex items-center justify-between py-1.5 text-sm">
      <span>{formation.name}</span>
      <span className="text-muted-foreground">
        {t("duration", { count: formation.duration_years })}
      </span>
    </li>
  );
}

/** Django serializes missing tuition as JSON `null` (never `undefined`) — the
 * `!= null` guard covers both, so a null-tuition school hides the row instead
 * of rendering "null–null €/an". */
function TuitionValue({ min, max }: { min: number; max: number }) {
  const t = useTranslations("ficheEcole");
  return <>{min === 0 && max === 0 ? t("tuitionFree") : t("tuitionRange", { min, max })}</>;
}

export function FicheEcole({
  school,
  variant = "card",
  className,
  isSelected,
  onSelect,
}: FicheEcoleProps) {
  const t = useTranslations("ficheEcole");
  const tuition =
    school.tuition_min_eur != null && school.tuition_max_eur != null
      ? { min: school.tuition_min_eur, max: school.tuition_max_eur }
      : null;

  // compare variant: compact horizontal layout with checkbox
  if (variant === "compare") {
    return (
      <article
        aria-label={t("ficheAria", { name: school.name })}
        className={cn("rounded-xl border bg-card", className)}
      >
        <label className="flex cursor-pointer items-start gap-3 rounded-xl p-3">
          <input
            type="checkbox"
            checked={isSelected ?? false}
            onChange={() => school.id && onSelect?.(school.id)}
            aria-label={t("selectAria", { name: school.name })}
            className="mt-1"
          />
          <div className="flex-1">
            <p className="font-medium">{school.name}</p>
            <p className="text-xs text-muted-foreground">{school.city}</p>
            <SelectivityStars index={school.selectivity_index} />
            {tuition && (
              <p className="mt-1 text-xs text-muted-foreground">
                <TuitionValue min={tuition.min} max={tuition.max} />
              </p>
            )}
          </div>
        </label>
      </article>
    );
  }

  // Heading levels: the expanded variant is the top-of-page content on both
  // /formations/{slug} (public SEO) and /schools/{slug} (authenticated) — no
  // other <h1> exists on those pages, so it must provide it (RGAA 9.1). The
  // card variant lives under a page-level <h1> (accueil, mes-paris) → <h2>.
  const HeadingTag = variant === "expanded" ? "h1" : "h2";
  const SectionHeadingTag = variant === "expanded" ? "h2" : "h3";

  // Distinguish "field omitted" (anonymous public payload — the
  // SchoolPublicSeoSerializer never sends `admission_stat`) from "field
  // present but null/empty" (authenticated payload, data not computed yet).
  // Anonymous visitors must not see a personalised "Tes chances" section.
  const hasAdmissionField = "admission_stat" in school;

  return (
    <article
      aria-label={t("ficheAria", { name: school.name })}
      className={cn("rounded-xl border bg-card", variant === "expanded" ? "p-6" : "p-4", className)}
    >
      {/* Header */}
      <div className="mb-3">
        <HeadingTag className="text-lg font-semibold">{school.name}</HeadingTag>
        <p className="text-sm text-muted-foreground">
          {school.city} · {school.region}
        </p>
      </div>

      {/* Key info as dl */}
      <dl className="mb-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
        <dt className="text-muted-foreground">{t("typeLabel")}</dt>
        <dd>{school.type}</dd>

        <dt className="text-muted-foreground">{t("accessLabel")}</dt>
        <dd>{school.public_private}</dd>

        <dt className="text-muted-foreground">{t("selectivityLabel")}</dt>
        <dd>
          <SelectivityStars index={school.selectivity_index} />
        </dd>

        {tuition && (
          <>
            <dt className="text-muted-foreground">{t("tuitionLabel")}</dt>
            <dd>
              <TuitionValue min={tuition.min} max={tuition.max} />
            </dd>
          </>
        )}

        {school.apprenticeship && (
          <>
            <dt className="text-muted-foreground">{t("apprenticeshipLabel")}</dt>
            <dd>{t("apprenticeshipAvailable")}</dd>
          </>
        )}
      </dl>

      {/* Formations list — only in expanded variant */}
      {variant === "expanded" && school.formations.length > 0 && (
        <section aria-label={t("formationsAria")}>
          <SectionHeadingTag className="mb-1 text-sm font-medium">
            {t("formationsTitle")}
          </SectionHeadingTag>
          <ul className="divide-y">
            {school.formations.map((f) => (
              <FormationItem key={f.id} formation={f} />
            ))}
          </ul>
        </section>
      )}

      {/* Débouchés — only in expanded variant */}
      {variant === "expanded" && school.top_debouches.length > 0 && (
        <section aria-label={t("debouchesAria")} className="mt-3">
          <SectionHeadingTag className="mb-1 text-sm font-medium">
            {t("debouchesTitle")}
          </SectionHeadingTag>
          <ul className="flex flex-wrap gap-1.5">
            {school.top_debouches.map((d) => (
              <li key={d} className="rounded-full bg-muted px-2.5 py-0.5 text-xs">
                {d}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Statistique d'admission — expanded variant, only when the payload
          carries the field (Story 4.5 AC1, AC5). Anonymous public payloads
          omit it entirely → section hidden instead of an empty "Tes chances
          d'admission" block. */}
      {variant === "expanded" && hasAdmissionField && (
        <section aria-label={t("admissionAria")} className="mt-4">
          <SectionHeadingTag className="mb-2 text-sm font-medium">
            {t("admissionTitle")}
          </SectionHeadingTag>
          {school.admission_stat ? (
            <AdmissionStatPoller
              initialStat={school.admission_stat}
              variant="medium"
              schoolName={school.name}
              schoolSlug={school.slug}
            />
          ) : (
            <p className="text-sm text-muted-foreground">{t("admissionUnavailable")}</p>
          )}
        </section>
      )}
    </article>
  );
}
