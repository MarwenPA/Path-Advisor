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

/** Canonical production origin — used for absolute URLs in JSON-LD/OG
 * markup. Story 7.4 (sitemap) will likely centralize this further; kept
 * here for now as the single source for this module. */
export const SITE_ORIGIN = "https://path-advisor.fr";

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

/** Schema.org `Occupation` — Story 7.3/7.4 AC (rich snippets). */
export function buildOccupationJsonLd(profession: Profession, url: string) {
  const jsonLd: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Occupation",
    name: profession.name,
    description: profession.description,
    url,
  };
  if (profession.median_salary_eur) {
    jsonLd.estimatedSalary = {
      "@type": "MonetaryAmountDistribution",
      currency: "EUR",
      median: profession.median_salary_eur,
    };
  }
  if (profession.sector) {
    jsonLd.occupationLocation = { "@type": "Country", name: "France" };
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
