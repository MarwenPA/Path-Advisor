import { describe, expect, it } from "vitest";

import { getOnboardingCopy, getPresumedLevel, type SchoolLevel } from "./level-adapter";

// Fixed "today" for deterministic tests — chosen so 15th-birthday boundaries
// fall cleanly on a non-ambiguous month.
const TODAY = new Date("2026-06-15T12:00:00Z");

describe("getPresumedLevel — bounds", () => {
  it("returns `college` when age < 15", () => {
    // 14 years old today
    expect(getPresumedLevel(new Date("2012-06-15"), TODAY)).toBe("college");
    // 13 years old
    expect(getPresumedLevel(new Date("2013-01-01"), TODAY)).toBe("college");
  });

  it("returns `lycee` when age is 15, 16, or 17", () => {
    expect(getPresumedLevel(new Date("2011-06-15"), TODAY)).toBe("lycee"); // exact 15
    expect(getPresumedLevel(new Date("2010-06-15"), TODAY)).toBe("lycee"); // 16
    expect(getPresumedLevel(new Date("2009-06-16"), TODAY)).toBe("lycee"); // 16 (birthday tomorrow)
  });

  it("returns `postbac` when age >= 18", () => {
    expect(getPresumedLevel(new Date("2008-06-15"), TODAY)).toBe("postbac"); // exact 18
    expect(getPresumedLevel(new Date("2000-01-01"), TODAY)).toBe("postbac"); // 26
  });

  it("handles the day-before-birthday correctly (still 14 → college)", () => {
    // Born 2011-06-16 → on 2026-06-15 they're still 14
    expect(getPresumedLevel(new Date("2011-06-16"), TODAY)).toBe("college");
  });
});

describe("getPresumedLevel — fallback to lycee", () => {
  it("returns lycee for null", () => {
    expect(getPresumedLevel(null, TODAY)).toBe("lycee");
  });

  it("returns lycee for undefined", () => {
    expect(getPresumedLevel(undefined, TODAY)).toBe("lycee");
  });

  it("returns lycee for invalid date string", () => {
    expect(getPresumedLevel("not-a-date", TODAY)).toBe("lycee");
    expect(getPresumedLevel("", TODAY)).toBe("lycee");
  });

  it("returns lycee for invalid Date object", () => {
    expect(getPresumedLevel(new Date("invalid"), TODAY)).toBe("lycee");
  });

  it("returns lycee for future birth date", () => {
    expect(getPresumedLevel(new Date("2030-01-01"), TODAY)).toBe("lycee");
  });

  it("accepts ISO string birth date", () => {
    expect(getPresumedLevel("2011-06-15T00:00:00Z", TODAY)).toBe("lycee");
  });
});

describe("getOnboardingCopy — snapshot per level (AC8)", () => {
  it.each<SchoolLevel>(["college", "lycee", "postbac"])(
    "ships a complete bundle for level=%s",
    (level) => {
      const bundle = getOnboardingCopy(level);
      expect(bundle.passionsTitle).toBeTruthy();
      expect(bundle.passionsSubtitle).toBeTruthy();
      expect(bundle.valeursTitle).toBeTruthy();
      expect(bundle.valeursSubtitle).toBeTruthy();
      expect(bundle.interetsTitle).toBeTruthy();
      expect(bundle.interetsSubtitle).toBeTruthy();
      expect(bundle.interetsPlaceholders).toHaveLength(3);
      bundle.interetsPlaceholders.forEach((p) => expect(p).toBeTruthy());
    },
  );

  it("uses Mehdi-friendly copy for college (no jargon scolaire)", () => {
    const bundle = getOnboardingCopy("college");
    expect(bundle.passionsTitle).toMatch(/branche/i);
    // No "discipline" / "matière" in the passions copy per persona guard
    expect(bundle.passionsTitle).not.toMatch(/discipline|matière/i);
    expect(bundle.passionsSubtitle).not.toMatch(/discipline/i);
  });

  it("uses Sarah/Léa lycée copy with `Qu'est-ce qui te plaît`", () => {
    expect(getOnboardingCopy("lycee").passionsTitle).toMatch(/qu'est-ce qui te plaît/i);
  });

  it("uses postbac copy with `Ce qui t'inspire`", () => {
    expect(getOnboardingCopy("postbac").passionsTitle).toMatch(/inspire/i);
  });

  it("interets placeholders differ across levels (level adapts vocabulary)", () => {
    const college = getOnboardingCopy("college").interetsPlaceholders[2];
    const lycee = getOnboardingCopy("lycee").interetsPlaceholders[2];
    const postbac = getOnboardingCopy("postbac").interetsPlaceholders[2];
    expect(college).not.toBe(lycee);
    expect(lycee).not.toBe(postbac);
  });

  it("snapshot — college bundle", () => {
    expect(getOnboardingCopy("college")).toMatchInlineSnapshot(`
      {
        "interetsPlaceholders": [
          "Ex. La chaîne YouTube de Marie Lopez sur la chimie, ou un podcast Choses à savoir…",
          "Ex. Le bouquin Sapiens, un film comme Hidden Figures, la série Mr Robot…",
          "Ex. La leçon où tu t'es pas ennuyé(e), un débat en cours…",
        ],
        "interetsSubtitle": "3 lignes max, format libre. Une chaîne YouTube, un podcast, un livre, une matière qui t'a marqué — ce que tu veux.",
        "interetsTitle": "Ce que tu suis, écoutes, regardes",
        "passionsSubtitle": "Choisis-en au moins 3. T'inquiète, tu pourras changer.",
        "passionsTitle": "Ce qui te branche, en vrai",
        "valeursSubtitle": "Choisis 3 à 5 valeurs. Y'a pas de bonne réponse.",
        "valeursTitle": "Ce qui te tient à cœur",
      }
    `);
  });

  it("snapshot — lycee bundle", () => {
    expect(getOnboardingCopy("lycee")).toMatchInlineSnapshot(`
      {
        "interetsPlaceholders": [
          "Ex. La chaîne YouTube de Marie Lopez sur la chimie, ou un podcast Choses à savoir…",
          "Ex. Le bouquin Sapiens, un film comme Hidden Figures, la série Mr Robot…",
          "Ex. La séquence sur la photosynthèse en 2nde, un débat en HGGSP, un TP de SVT…",
        ],
        "interetsSubtitle": "3 lignes max, format libre. Une chaîne YouTube, un podcast, un livre, une matière qui t'a marqué — ce que tu veux.",
        "interetsTitle": "Ce que tu suis, écoutes, regardes",
        "passionsSubtitle": "Choisis-en au moins 3. T'inquiète, tu pourras changer.",
        "passionsTitle": "Qu'est-ce qui te plaît, vraiment ?",
        "valeursSubtitle": "Choisis 3 à 5 valeurs. Y'a pas de bonne réponse.",
        "valeursTitle": "Ce qui compte le plus pour toi",
      }
    `);
  });

  it("snapshot — postbac bundle", () => {
    expect(getOnboardingCopy("postbac")).toMatchInlineSnapshot(`
      {
        "interetsPlaceholders": [
          "Ex. Une newsletter pro, un podcast comme Génération Do It Yourself…",
          "Ex. Un essai marquant, un film, une série…",
          "Ex. Un cours marquant en L1, un projet de stage, une lecture pro…",
        ],
        "interetsSubtitle": "3 lignes max, format libre. Une newsletter, un podcast, un livre pro, un cours qui t'a marqué — ce que tu veux.",
        "interetsTitle": "Ce que tu suis, écoutes, regardes",
        "passionsSubtitle": "Choisis-en au moins 3. Tu pourras revenir les modifier à tout moment.",
        "passionsTitle": "Ce qui t'inspire en ce moment",
        "valeursSubtitle": "Choisis 3 à 5 valeurs. Pas de bonne ou mauvaise réponse.",
        "valeursTitle": "Ce qui compte le plus pour toi",
      }
    `);
  });
});
