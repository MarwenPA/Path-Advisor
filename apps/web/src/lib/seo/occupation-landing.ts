/**
 * Shared helpers for the long-tail SEO landing pages — Story 7.3.
 *
 * FAQ entries are generated FROM the fiche métier's own real fields
 * (median salary, requirements, prospects, level compatibility) — never
 * fabricated facts — so the `FAQPage` JSON-LD markup always mirrors
 * content that's actually visible on the page (a Google Rich Results
 * requirement, not just good practice).
 */
import type { Profession } from "@/components/professions/types";

/** Canonical production origin. Kept as its own constant so `robots.ts`
 * can detect "this deploy is NOT production" (Epic 7 review: a staging
 * deploy must not advertise production canonicals nor let itself be
 * indexed). */
export const PRODUCTION_ORIGIN = "https://path-advisor.fr";

/** Origin used for absolute URLs in canonicals/JSON-LD/OG markup and the
 * sitemap. Epic 7 review fix: previously hardcoded to production, so any
 * staging deploy emitted production URLs everywhere. `NEXT_PUBLIC_` prefix
 * so the value is inlined consistently in both server and client bundles. */
export const SITE_ORIGIN = process.env.NEXT_PUBLIC_SITE_ORIGIN ?? PRODUCTION_ORIGIN;

/** Valid niveau URL slugs for `/{niveau}/quel-bac-pour-{metier}` (Story
 * 7.3 AC2), mapped to the backend `Parcours.NiveauScolaire` enum. Lives
 * here (not in the page file) so `app/sitemap.ts` can enumerate the same
 * slugs without importing a page module — emitting a niveau the page
 * doesn't recognize would put 404s in the sitemap. Labels stay in
 * `messages/fr.json#quelBacPourPage.niveauLabels` (Story 7.7). */
export const NIVEAU_SLUGS: Record<string, { apiValue: string }> = {
  "3eme": { apiValue: "troisieme_bac_pro" },
  "terminale-generale": { apiValue: "terminale_generale" },
  "terminale-technologique": { apiValue: "terminale_technologique" },
  "terminale-pro": { apiValue: "terminale_pro" },
};

export interface FaqEntry {
  question: string;
  answer: string;
}

const LEVEL_LABELS: Record<string, string> = {
  lycee_1ere_tle_general: "en filière générale (1ère/Terminale)",
  lycee_1ere_tle_techno: "en filière technologique (1ère/Terminale)",
  lycee_pro: "en filière professionnelle",
  postbac: "après le bac",
};

function formatSalary(profession: Profession): string | null {
  if (profession.salary_range_json) {
    const { min, max } = profession.salary_range_json;
    return `entre ${min.toLocaleString("fr-FR")} € et ${max.toLocaleString("fr-FR")} € brut par an`;
  }
  if (profession.median_salary_eur) {
    return `environ ${profession.median_salary_eur.toLocaleString("fr-FR")} € brut par an (médiane)`;
  }
  return null;
}

export function buildOccupationFaq(profession: Profession): FaqEntry[] {
  const faq: FaqEntry[] = [];

  const salary = formatSalary(profession);
  if (salary) {
    faq.push({
      question: `Quel est le salaire d'un·e ${profession.name} ?`,
      answer: `Le salaire d'un·e ${profession.name} se situe ${salary}.`,
    });
  }

  const studies = profession.requirements_json.filter((r) => r.type === "studies");
  if (studies.length > 0) {
    faq.push({
      question: `Quelles études faire pour devenir ${profession.name} ?`,
      answer: `Les parcours d'études les plus courants sont : ${studies.map((s) => s.label).join(", ")}.`,
    });
  }

  if (profession.prospects_text) {
    faq.push({
      question: `Quelles perspectives d'évolution pour un·e ${profession.name} ?`,
      answer: profession.prospects_text,
    });
  }

  if (profession.level_compatibility.length > 0) {
    const labels = profession.level_compatibility.map((l) => LEVEL_LABELS[l] ?? l);
    faq.push({
      question: `Quel bac choisir pour devenir ${profession.name} ?`,
      answer: `Ce métier est accessible ${labels.join(" ou ")}.`,
    });
  }

  return faq;
}

/**
 * Schema.org `Occupation` — Story 7.3/7.4 AC (rich snippets).
 *
 * Epic 7 review fixes (Google "Estimated salary" structured-data reqs):
 * - `MonetaryAmountDistribution` REQUIRES `duration` — our figures are
 *   annual gross, so `"P1Y"` (ISO 8601), else no rich result at all.
 * - `salary_range_json` now feeds `percentile10`/`percentile90` and acts
 *   as the fallback when `median_salary_eur` is absent (it was ignored).
 * - empty `description` is omitted rather than emitted as `""`.
 * - `occupationLocation` was `{"@type":"Country"}` gated on the unrelated
 *   `sector` field — Google requires City granularity, which we don't
 *   have for a nationwide métier, so it's dropped entirely (a
 *   non-compliant value is worse than none). `industry` keeps its
 *   (correct) `sector` gate.
 */
export function buildOccupationJsonLd(profession: Profession, url: string) {
  const jsonLd: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Occupation",
    name: profession.name,
    url,
  };
  if (profession.description) {
    jsonLd.description = profession.description;
  }
  if (profession.median_salary_eur || profession.salary_range_json) {
    // Array form + `name: "base"` per Google's own Occupation example.
    jsonLd.estimatedSalary = [
      {
        "@type": "MonetaryAmountDistribution",
        name: "base",
        currency: "EUR",
        duration: "P1Y",
        ...(profession.median_salary_eur ? { median: profession.median_salary_eur } : {}),
        ...(profession.salary_range_json
          ? {
              percentile10: profession.salary_range_json.min,
              percentile90: profession.salary_range_json.max,
            }
          : {}),
      },
    ];
  }
  if (profession.sector) {
    jsonLd.industry = profession.sector;
  }
  return jsonLd;
}

/** Schema.org `EducationalOrganization` — Story 7.4 AC (rich snippets on
 * `/formations/{slug}`). Minimal fields mapped straight from `School`. */
export function buildEducationalOrganizationJsonLd(
  school: {
    name: string;
    description: string;
    city: string;
    official_url: string;
  },
  url: string,
) {
  return {
    "@context": "https://schema.org",
    "@type": "EducationalOrganization",
    name: school.name,
    description: school.description,
    address: { "@type": "PostalAddress", addressLocality: school.city, addressCountry: "FR" },
    url: school.official_url || url,
  };
}

/** Schema.org `FAQPage` — must mirror `faq` exactly (Google Rich Results
 * requirement: markup content must match visible content). */
export function buildFaqPageJsonLd(faq: FaqEntry[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((entry) => ({
      "@type": "Question",
      name: entry.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: entry.answer,
      },
    })),
  };
}
