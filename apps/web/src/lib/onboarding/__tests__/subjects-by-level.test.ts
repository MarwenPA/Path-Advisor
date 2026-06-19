import { describe, expect, it } from "vitest";

import {
  getOptionalSubjectsForLevel,
  getSubjectsForLevel,
  SUBJECTS_REF_VERSION,
} from "../subjects-by-level";

describe("getSubjectsForLevel", () => {
  it("returns non-empty list for lycee_terminale general", () => {
    const subjects = getSubjectsForLevel("lycee_terminale", "general", [
      "mathematiques",
      "svt",
    ]);
    expect(subjects.length).toBeGreaterThan(0);
    expect(subjects.every((s) => s.id && s.label)).toBe(true);
  });

  it("includes declared specialites in the list for terminale general", () => {
    const subjects = getSubjectsForLevel("lycee_terminale", "general", [
      "mathematiques",
      "svt",
    ]);
    const ids = subjects.map((s) => s.id);
    expect(ids).toContain("mathematiques");
    expect(ids).toContain("svt");
  });

  it("returns non-empty list for college_3eme", () => {
    const subjects = getSubjectsForLevel("college_3eme");
    expect(subjects.length).toBeGreaterThan(5);
  });

  it("returns non-empty list for lycee_2nde", () => {
    const subjects = getSubjectsForLevel("lycee_2nde");
    expect(subjects.length).toBeGreaterThan(0);
  });

  it("returns non-empty list for lycee_terminale techno (STMG)", () => {
    const subjects = getSubjectsForLevel(
      "lycee_terminale",
      "technologique",
      [],
      "STMG"
    );
    expect(subjects.length).toBeGreaterThan(0);
  });

  it("returns empty array for postbac (manual all)", () => {
    const subjects = getSubjectsForLevel("postbac");
    expect(subjects).toHaveLength(0);
  });

  it("marks specialites with is_specialite=true", () => {
    const subjects = getSubjectsForLevel("lycee_terminale", "general", [
      "mathematiques",
    ]);
    const maths = subjects.find((s) => s.id === "mathematiques");
    expect(maths?.is_specialite).toBe(true);
  });

  it("marks tronc commun subjects with is_specialite=false", () => {
    const subjects = getSubjectsForLevel("lycee_terminale", "general", [
      "mathematiques",
    ]);
    const philo = subjects.find((s) => s.id === "philosophie");
    expect(philo?.is_specialite).toBe(false);
  });
});

describe("getOptionalSubjectsForLevel", () => {
  it("returns a list of optional subjects for lycee general", () => {
    const opts = getOptionalSubjectsForLevel("lycee_terminale", "general");
    expect(opts.length).toBeGreaterThan(0);
    expect(opts.every((s) => s.is_optional)).toBe(true);
  });

  it("includes Latin in optional subjects for lycee", () => {
    const opts = getOptionalSubjectsForLevel("lycee_terminale", "general");
    expect(opts.some((s) => s.id === "latin")).toBe(true);
  });
});

describe("SUBJECTS_REF_VERSION", () => {
  it("is a non-empty string", () => {
    expect(SUBJECTS_REF_VERSION).toBeTruthy();
    expect(typeof SUBJECTS_REF_VERSION).toBe("string");
  });
});
