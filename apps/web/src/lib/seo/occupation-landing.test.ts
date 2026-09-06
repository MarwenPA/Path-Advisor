/**
 * Occupation-landing SEO helper tests — Story 7.3.
 */
import { describe, expect, it } from "vitest";

import type { Profession } from "@/components/professions/types";

import {
  buildFaqPageJsonLd,
  buildOccupationFaq,
  buildOccupationJsonLd,
} from "./occupation-landing";

const PROFESSION: Profession = {
  slug: "infirmier-test",
  name: "Infirmier·ère",
  description: "Description du métier d'infirmier.",
  daily_routine: "Une journée type.",
  requirements_json: [
    { type: "studies", label: "DEI 3 ans" },
    { type: "quality", label: "Empathie" },
  ],
  prospects_text: "Cadre de santé, formateur.",
  median_salary_eur: 32000,
  signals_json: { passions: [], valeurs: [], specialites: [] },
  level_compatibility: ["lycee_1ere_tle_general"],
  sector: "santé",
};

describe("buildOccupationFaq", () => {
  it("includes a salary question grounded in median_salary_eur", () => {
    const faq = buildOccupationFaq(PROFESSION);
    const salaryEntry = faq.find((f) => f.question.includes("salaire"));
    expect(salaryEntry?.answer).toMatch(/32.000/);
  });

  it("includes a studies question listing only 'studies' requirements", () => {
    const faq = buildOccupationFaq(PROFESSION);
    const studiesEntry = faq.find((f) => f.question.includes("études"));
    expect(studiesEntry?.answer).toContain("DEI 3 ans");
    expect(studiesEntry?.answer).not.toContain("Empathie");
  });

  it("includes a prospects question using prospects_text verbatim", () => {
    const faq = buildOccupationFaq(PROFESSION);
    const prospectsEntry = faq.find((f) => f.question.includes("évolution"));
    expect(prospectsEntry?.answer).toBe("Cadre de santé, formateur.");
  });

  it("omits the salary question when no salary data exists", () => {
    const faq = buildOccupationFaq({
      ...PROFESSION,
      median_salary_eur: null,
      salary_range_json: null,
    });
    expect(faq.find((f) => f.question.includes("salaire"))).toBeUndefined();
  });
});

describe("buildOccupationJsonLd", () => {
  it("builds a valid Schema.org Occupation object", () => {
    const jsonLd = buildOccupationJsonLd(PROFESSION, "https://path-advisor.fr/devenir-infirmier");
    expect(jsonLd["@type"]).toBe("Occupation");
    expect(jsonLd.name).toBe("Infirmier·ère");
    expect(jsonLd.url).toBe("https://path-advisor.fr/devenir-infirmier");
  });
});

describe("buildFaqPageJsonLd", () => {
  it("mirrors the FAQ entries exactly (Google Rich Results requirement)", () => {
    const faq = buildOccupationFaq(PROFESSION);
    const jsonLd = buildFaqPageJsonLd(faq);
    expect(jsonLd["@type"]).toBe("FAQPage");
    expect(jsonLd.mainEntity).toHaveLength(faq.length);
    expect(jsonLd.mainEntity[0].name).toBe(faq[0].question);
    expect(jsonLd.mainEntity[0].acceptedAnswer.text).toBe(faq[0].answer);
  });
});
