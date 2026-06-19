/**
 * Tests for Story 2.2 — referential integrity.
 * Mirrors: apps/api/apps/students/tests/test_onboarding_step2.py::test_level_ids_*
 */

import { describe, it, expect } from "vitest";
import {
  LEVELS,
  TRACKS_3EME,
  FILIERES_LYCEE,
  SOUS_FILIERES_TECHNO,
  SPECIALITES_LYCEE,
  SPECIALITES_BAC_PRO,
  POSTBAC_YEARS,
  POSTBAC_FORMATIONS,
  expectedSpecCount,
  requiresSousFiliere,
  calendarHint,
} from "./levels";

describe("LEVELS referential", () => {
  it("has exactly 5 items", () => expect(LEVELS).toHaveLength(5));
  it("has unique IDs", () => {
    const ids = LEVELS.map((l) => l.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
  it("all items have label and description", () => {
    LEVELS.forEach((l) => {
      expect(l.label).toBeTruthy();
      expect(l.description).toBeTruthy();
    });
  });
});

describe("TRACKS_3EME referential", () => {
  it("has exactly 4 items", () => expect(TRACKS_3EME).toHaveLength(4));
  it("includes undecided as last item", () => {
    expect(TRACKS_3EME[TRACKS_3EME.length - 1].id).toBe("undecided");
  });
});

describe("FILIERES_LYCEE referential", () => {
  it("has exactly 3 items", () => expect(FILIERES_LYCEE).toHaveLength(3));
});

describe("SOUS_FILIERES_TECHNO referential", () => {
  it("has exactly 7 items", () => expect(SOUS_FILIERES_TECHNO).toHaveLength(7));
  it("includes STMG and STI2D", () => {
    const ids = SOUS_FILIERES_TECHNO.map((s) => s.id);
    expect(ids).toContain("STMG");
    expect(ids).toContain("STI2D");
  });
});

describe("SPECIALITES_LYCEE referential", () => {
  it("has exactly 13 items (official EN 2026)", () => expect(SPECIALITES_LYCEE).toHaveLength(13));
  it("has unique IDs", () => {
    const ids = SPECIALITES_LYCEE.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
  it("includes mathematiques, svt, hggsp", () => {
    const ids = SPECIALITES_LYCEE.map((s) => s.id);
    expect(ids).toContain("mathematiques");
    expect(ids).toContain("svt");
    expect(ids).toContain("hggsp");
  });
  it("all items have shortLabel", () => {
    SPECIALITES_LYCEE.forEach((s) => expect(s.shortLabel).toBeTruthy());
  });
});

describe("SPECIALITES_BAC_PRO referential", () => {
  it("has exactly 15 items", () => expect(SPECIALITES_BAC_PRO).toHaveLength(15));
  it("has unique IDs", () => {
    const ids = SPECIALITES_BAC_PRO.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("POSTBAC_YEARS referential", () => {
  it("has exactly 6 items", () => expect(POSTBAC_YEARS).toHaveLength(6));
  it("includes pause option", () => {
    expect(POSTBAC_YEARS.map((y) => y.id)).toContain("pause");
  });
});

describe("POSTBAC_FORMATIONS referential", () => {
  it("has exactly 9 items", () => expect(POSTBAC_FORMATIONS).toHaveLength(9));
  it("includes aucune as last", () => {
    expect(POSTBAC_FORMATIONS[POSTBAC_FORMATIONS.length - 1].id).toBe("aucune");
  });
});

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

describe("expectedSpecCount", () => {
  it("returns 3 for 1ère général", () => {
    expect(expectedSpecCount("lycee_1ere", "general")).toBe(3);
  });
  it("returns 2 for Terminale général", () => {
    expect(expectedSpecCount("lycee_terminale", "general")).toBe(2);
  });
  it("returns 1 for 2nde pro", () => {
    expect(expectedSpecCount("lycee_2nde", "pro")).toBe(1);
  });
  it("returns null for Terminale techno", () => {
    expect(expectedSpecCount("lycee_terminale", "techno")).toBeNull();
  });
  it("returns null for 2nde général", () => {
    expect(expectedSpecCount("lycee_2nde", "general")).toBeNull();
  });
  it("returns null for postbac", () => {
    expect(expectedSpecCount("postbac", null)).toBeNull();
  });
});

describe("requiresSousFiliere", () => {
  it("returns true for 1ère techno", () => {
    expect(requiresSousFiliere("lycee_1ere", "techno")).toBe(true);
  });
  it("returns true for Terminale techno", () => {
    expect(requiresSousFiliere("lycee_terminale", "techno")).toBe(true);
  });
  it("returns false for 2nde techno", () => {
    expect(requiresSousFiliere("lycee_2nde", "techno")).toBe(false);
  });
  it("returns false for 1ère général", () => {
    expect(requiresSousFiliere("lycee_1ere", "general")).toBe(false);
  });
  it("returns false for 3ème", () => {
    expect(requiresSousFiliere("college_3eme", null)).toBe(false);
  });
});

describe("calendarHint", () => {
  it("mentions Affelnet for 3ème", () => {
    expect(calendarHint("college_3eme", "pro")).toContain("Affelnet");
  });
  it("mentions Parcoursup for Terminale", () => {
    expect(calendarHint("lycee_terminale", null)).toContain("Parcoursup");
  });
  it("returns a string for postbac", () => {
    expect(typeof calendarHint("postbac", null)).toBe("string");
  });
});
