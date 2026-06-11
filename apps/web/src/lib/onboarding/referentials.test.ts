import { describe, it, expect } from "vitest";

import {
  CUSTOM_PASSION_PREFIX,
  INTERETS_SUGGESTIONS,
  MAX_CUSTOM_PASSIONS,
  MAX_PASSIONS_TOTAL,
  PASSIONS_CATEGORIES,
  PASSION_IDS,
  VALEURS,
  VALEUR_IDS,
  filterPassions,
  interetsRecordSchema,
  makeCustomPassionId,
  passionIdSchema,
  passionsArraySchema,
  valeurIdSchema,
  valeursArraySchema,
} from "./referentials";

describe("referentials — structural invariants (T1)", () => {
  it("ships 20 passions categories", () => {
    expect(PASSIONS_CATEGORIES).toHaveLength(20);
  });

  it("ships 12 valeurs", () => {
    expect(VALEURS).toHaveLength(12);
  });

  it("ships 5 suggestions per intérêt field (3 fields)", () => {
    expect(Object.keys(INTERETS_SUGGESTIONS)).toEqual(["1", "2", "3"]);
    expect(INTERETS_SUGGESTIONS[1]).toHaveLength(5);
    expect(INTERETS_SUGGESTIONS[2]).toHaveLength(5);
    expect(INTERETS_SUGGESTIONS[3]).toHaveLength(5);
  });

  it("passion IDs are unique", () => {
    expect(new Set(PASSION_IDS).size).toBe(PASSION_IDS.length);
  });

  it("valeur IDs are unique", () => {
    expect(new Set(VALEUR_IDS).size).toBe(VALEUR_IDS.length);
  });

  it("all passion labels < 30 chars (UX chip width)", () => {
    for (const p of PASSIONS_CATEGORIES) {
      expect(p.label.length, `label "${p.label}"`).toBeLessThan(30);
    }
  });

  it("all valeur descriptions < 80 chars (UX card height)", () => {
    for (const v of VALEURS) {
      expect(v.description.length, `desc "${v.label}"`).toBeLessThan(80);
    }
  });

  it("all passion IDs are kebab-case ASCII", () => {
    for (const id of PASSION_IDS) {
      expect(id, `id ${id}`).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
    }
  });
});

describe("Zod — passionIdSchema", () => {
  it("accepts a known referential ID", () => {
    expect(passionIdSchema.safeParse("sciences-nature").success).toBe(true);
  });

  it("accepts a valid custom: ID", () => {
    expect(passionIdSchema.safeParse("custom:graphql").success).toBe(true);
    expect(passionIdSchema.safeParse("custom:justice-clima").success).toBe(true);
  });

  it("rejects unknown bare IDs", () => {
    expect(passionIdSchema.safeParse("unicorns").success).toBe(false);
  });

  it("rejects custom: with bad slug", () => {
    expect(passionIdSchema.safeParse("custom:Avec Espaces").success).toBe(false);
    expect(passionIdSchema.safeParse("custom:-leading").success).toBe(false);
    expect(passionIdSchema.safeParse("custom:trailing-").success).toBe(false);
    expect(passionIdSchema.safeParse("custom:").success).toBe(false);
  });

  it("rejects custom: > 30 chars", () => {
    const slug = "a".repeat(31);
    expect(passionIdSchema.safeParse(`${CUSTOM_PASSION_PREFIX}${slug}`).success).toBe(false);
  });
});

describe("Zod — valeurIdSchema", () => {
  it("accepts a known valeur ID", () => {
    expect(valeurIdSchema.safeParse("justice-sociale").success).toBe(true);
  });

  it("rejects unknown valeur ID", () => {
    expect(valeurIdSchema.safeParse("custom:patience").success).toBe(false);
    expect(valeurIdSchema.safeParse("bogus").success).toBe(false);
  });
});

describe("Zod — passionsArraySchema", () => {
  it("accepts up to 8 entries", () => {
    const eight = PASSION_IDS.slice(0, MAX_PASSIONS_TOTAL);
    expect(passionsArraySchema.safeParse(eight).success).toBe(true);
  });

  it("rejects > 8 entries", () => {
    const nine = PASSION_IDS.slice(0, MAX_PASSIONS_TOTAL + 1);
    expect(passionsArraySchema.safeParse(nine).success).toBe(false);
  });

  it("rejects > 5 custom entries", () => {
    const six = Array.from({ length: MAX_CUSTOM_PASSIONS + 1 }, (_, i) => `custom:c${i}`);
    expect(passionsArraySchema.safeParse(six).success).toBe(false);
  });

  it("rejects duplicates", () => {
    expect(passionsArraySchema.safeParse(["musique", "musique"]).success).toBe(false);
  });
});

describe("Zod — valeursArraySchema", () => {
  it("accepts 3 valeurs", () => {
    expect(valeursArraySchema.safeParse(["justice-sociale", "creativite", "sens-utilite"]).success).toBe(true);
  });

  it("rejects > 5 valeurs", () => {
    expect(valeursArraySchema.safeParse(VALEUR_IDS.slice(0, 6)).success).toBe(false);
  });

  it("rejects duplicates", () => {
    expect(valeursArraySchema.safeParse(["aventure", "aventure"]).success).toBe(false);
  });
});

describe("Zod — interetsRecordSchema", () => {
  it("accepts nulls (all-empty allowed per AC4)", () => {
    expect(interetsRecordSchema.safeParse({ "1": null, "2": null, "3": null }).success).toBe(true);
  });

  it("accepts mixed strings + nulls", () => {
    expect(
      interetsRecordSchema.safeParse({ "1": "Podcast Choses à savoir", "2": null, "3": "TP SVT" }).success,
    ).toBe(true);
  });

  it("rejects strings > 200 chars", () => {
    const long = "a".repeat(201);
    expect(interetsRecordSchema.safeParse({ "1": long, "2": null, "3": null }).success).toBe(false);
  });
});

describe("filterPassions", () => {
  it("returns all when query is empty", () => {
    expect(filterPassions("")).toHaveLength(PASSIONS_CATEGORIES.length);
    expect(filterPassions("   ")).toHaveLength(PASSIONS_CATEGORIES.length);
  });

  it("matches on label (case-insensitive)", () => {
    const hits = filterPassions("ciné");
    expect(hits.some((p) => p.id === "cinema-series")).toBe(true);
  });

  it("matches on alias", () => {
    const hits = filterPassions("code");
    expect(hits.some((p) => p.id === "tech-code")).toBe(true);
  });

  it("matches accent-insensitively", () => {
    const hits = filterPassions("creation");
    expect(hits.some((p) => p.id === "arts-creation")).toBe(true);
  });

  it("returns empty for no match", () => {
    expect(filterPassions("zzzyyy_no_match")).toHaveLength(0);
  });
});

describe("makeCustomPassionId", () => {
  it("normalizes to custom:<slug>", () => {
    expect(makeCustomPassionId("Justice clima")).toBe("custom:justice-clima");
    expect(makeCustomPassionId("  Hand BALL  ")).toBe("custom:hand-ball");
  });

  it("strips accents", () => {
    expect(makeCustomPassionId("Élevage")).toBe("custom:elevage");
  });

  it("returns null for empty / whitespace-only", () => {
    expect(makeCustomPassionId("")).toBeNull();
    expect(makeCustomPassionId("   ")).toBeNull();
  });

  it("returns null when slug exceeds 30 chars", () => {
    expect(makeCustomPassionId("a".repeat(31))).toBeNull();
  });
});
