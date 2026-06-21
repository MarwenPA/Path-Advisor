import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";

import { useParcoursFilters } from "../useParcoursFilters";
import { DEFAULT_FILTERS } from "../FilterBar";
import type { Parcours } from "../types";

// ─── Fixtures ─────────────────────────────────────────────────────────────────

function makeParcours(overrides: Partial<Parcours> = {}): Parcours {
  return {
    id: overrides.id ?? "p1",
    nodes: [],
    edges: [],
    target_school_name: "Ecole Test",
    target_school_tuition_max: overrides.target_school_tuition_max ?? 8000,
    target_school_selectivity: overrides.target_school_selectivity ?? 3,
    target_school_apprenticeship: overrides.target_school_apprenticeship ?? false,
    target_school_internship: overrides.target_school_internship ?? false,
    ...overrides,
  };
}

const FREE_SCHOOL = makeParcours({
  id: "free",
  target_school_tuition_max: 0,
  target_school_name: "Lycee Public",
});

const CHEAP_SCHOOL = makeParcours({
  id: "cheap",
  target_school_tuition_max: 4000,
  target_school_name: "BTS Pas Cher",
});

const MID_SCHOOL = makeParcours({
  id: "mid",
  target_school_tuition_max: 7500,
  target_school_name: "Ecole Moyen",
});

const EXPENSIVE_SCHOOL = makeParcours({
  id: "expensive",
  target_school_tuition_max: 15000,
  target_school_name: "Grande Ecole Chere",
});

const NULL_COST_SCHOOL = makeParcours({
  id: "null-cost",
  target_school_tuition_max: null,
  target_school_name: "Ecole Inconnue",
});

const TRES_SELECTIF = makeParcours({
  id: "sel-1",
  target_school_selectivity: 1,
  target_school_name: "Polytechnique",
});

const SELECTIF = makeParcours({
  id: "sel-2",
  target_school_selectivity: 2,
  target_school_name: "CPGE Selectif",
});

const ACCESSIBLE = makeParcours({
  id: "sel-4",
  target_school_selectivity: 4,
  target_school_name: "IUT Accessible",
});

const OUVERT = makeParcours({
  id: "sel-5",
  target_school_selectivity: 5,
  target_school_name: "Universite Ouverte",
});

const APPRENTICESHIP_SCHOOL = makeParcours({
  id: "app",
  target_school_apprenticeship: true,
  target_school_name: "CFA Alternance",
});

const INTERNSHIP_SCHOOL = makeParcours({
  id: "int",
  target_school_internship: true,
  target_school_name: "Ecole Internat",
});

const ALL_SCHOOLS = [
  FREE_SCHOOL,
  CHEAP_SCHOOL,
  MID_SCHOOL,
  EXPENSIVE_SCHOOL,
  NULL_COST_SCHOOL,
  TRES_SELECTIF,
  SELECTIF,
  ACCESSIBLE,
  OUVERT,
  APPRENTICESHIP_SCHOOL,
  INTERNSHIP_SCHOOL,
];

// ─── Tests ────────────────────────────────────────────────────────────────────

function filter(parcours: Parcours[], filters = DEFAULT_FILTERS) {
  const { result } = renderHook(() => useParcoursFilters(parcours, filters));
  return result.current;
}

describe("useParcoursFilters", () => {
  it("no filter returns all items", () => {
    const result = filter(ALL_SCHOOLS);
    expect(result).toHaveLength(ALL_SCHOOLS.length);
  });

  // ── Cost ──────────────────────────────────────────────────────────────────

  it("cost=free keeps only tuition_max === 0", () => {
    const result = filter([FREE_SCHOOL, CHEAP_SCHOOL, NULL_COST_SCHOOL], {
      ...DEFAULT_FILTERS,
      cost: "free",
    });
    expect(result).toEqual([FREE_SCHOOL]);
  });

  it("cost=under5k keeps tuition_max <= 5000 (excludes null)", () => {
    const result = filter([FREE_SCHOOL, CHEAP_SCHOOL, MID_SCHOOL, NULL_COST_SCHOOL], {
      ...DEFAULT_FILTERS,
      cost: "under5k",
    });
    // FREE_SCHOOL (0) and CHEAP_SCHOOL (4000) pass; MID_SCHOOL (7500) and null fail
    expect(result.map((p) => p.id)).toEqual(["free", "cheap"]);
  });

  it("cost=under10k keeps tuition_max <= 10000 (excludes null)", () => {
    const result = filter(
      [FREE_SCHOOL, CHEAP_SCHOOL, MID_SCHOOL, EXPENSIVE_SCHOOL, NULL_COST_SCHOOL],
      { ...DEFAULT_FILTERS, cost: "under10k" },
    );
    expect(result.map((p) => p.id)).toEqual(["free", "cheap", "mid"]);
  });

  // ── Selectivity ───────────────────────────────────────────────────────────

  it("selectivity=very_selective keeps only index=1", () => {
    const result = filter([TRES_SELECTIF, SELECTIF, ACCESSIBLE, OUVERT], {
      ...DEFAULT_FILTERS,
      selectivity: "very_selective",
    });
    expect(result).toEqual([TRES_SELECTIF]);
  });

  it("selectivity=selective keeps index=2 and 3", () => {
    const p3 = makeParcours({ id: "sel-3", target_school_selectivity: 3 });
    const result = filter([TRES_SELECTIF, SELECTIF, p3, ACCESSIBLE], {
      ...DEFAULT_FILTERS,
      selectivity: "selective",
    });
    expect(result.map((p) => p.id)).toEqual(["sel-2", "sel-3"]);
  });

  it("selectivity=accessible keeps only index=4", () => {
    const result = filter([SELECTIF, ACCESSIBLE, OUVERT], {
      ...DEFAULT_FILTERS,
      selectivity: "accessible",
    });
    expect(result).toEqual([ACCESSIBLE]);
  });

  it("selectivity=open keeps only index=5", () => {
    const result = filter([ACCESSIBLE, OUVERT, TRES_SELECTIF], {
      ...DEFAULT_FILTERS,
      selectivity: "open",
    });
    expect(result).toEqual([OUVERT]);
  });

  // ── Mode ──────────────────────────────────────────────────────────────────

  it("mode=apprenticeship keeps only apprenticeship=true", () => {
    const result = filter([APPRENTICESHIP_SCHOOL, INTERNSHIP_SCHOOL, FREE_SCHOOL], {
      ...DEFAULT_FILTERS,
      mode: ["apprenticeship"],
    });
    expect(result).toEqual([APPRENTICESHIP_SCHOOL]);
  });

  it("mode=internship keeps only internship=true", () => {
    const result = filter([APPRENTICESHIP_SCHOOL, INTERNSHIP_SCHOOL, FREE_SCHOOL], {
      ...DEFAULT_FILTERS,
      mode: ["internship"],
    });
    expect(result).toEqual([INTERNSHIP_SCHOOL]);
  });

  it("mode=[apprenticeship, internship] keeps schools with both flags", () => {
    const both = makeParcours({
      id: "both",
      target_school_apprenticeship: true,
      target_school_internship: true,
    });
    const result = filter([APPRENTICESHIP_SCHOOL, INTERNSHIP_SCHOOL, both, FREE_SCHOOL], {
      ...DEFAULT_FILTERS,
      mode: ["apprenticeship", "internship"],
    });
    expect(result).toEqual([both]);
  });

  // ── Combined ──────────────────────────────────────────────────────────────

  it("combined cost=free + selectivity=very_selective", () => {
    const freeSelectif = makeParcours({
      id: "free-selectif",
      target_school_tuition_max: 0,
      target_school_selectivity: 1,
      target_school_name: "Ecole Gratuite Selectif",
    });
    const result = filter([FREE_SCHOOL, TRES_SELECTIF, freeSelectif], {
      ...DEFAULT_FILTERS,
      cost: "free",
      selectivity: "very_selective",
    });
    expect(result).toEqual([freeSelectif]);
  });
});
