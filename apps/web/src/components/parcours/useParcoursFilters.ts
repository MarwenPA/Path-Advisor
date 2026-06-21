import { useMemo } from "react";

import type { ParcoursFilters } from "./FilterBar";
import type { Parcours } from "./types";

/**
 * Maps selectivity filter values to their allowed selectivity_index values.
 *
 * selectivity_index: 1 = tres selectif (grandes ecoles), 5 = non selectif (universite ouverte)
 * Story 4.6 mapping (from spec):
 *   very_selective -> [1]
 *   selective      -> [2, 3]
 *   accessible     -> [4]
 *   open           -> [5]
 */
const SELECTIVITY_MAP: Record<Exclude<ParcoursFilters["selectivity"], "all">, number[]> = {
  very_selective: [1],
  selective: [2, 3],
  accessible: [4],
  open: [5],
};

/**
 * useParcoursFilters — pure client-side filtering of a parcours array.
 *
 * Returns a memoised sub-array that respects the active filters.
 * All filter logic runs in O(n) per change; no async calls.
 */
export function useParcoursFilters(parcoursList: Parcours[], filters: ParcoursFilters): Parcours[] {
  return useMemo(() => {
    return parcoursList.filter((p) => {
      // ── Cost filter ─────────────────────────────────────────────────────────
      if (filters.cost === "free") {
        if (p.target_school_tuition_max !== 0) return false;
      } else if (filters.cost === "under5k") {
        if (p.target_school_tuition_max === null) return false;
        if (p.target_school_tuition_max > 5000) return false;
      } else if (filters.cost === "under10k") {
        if (p.target_school_tuition_max === null) return false;
        if (p.target_school_tuition_max > 10000) return false;
      }

      // ── Selectivity filter ──────────────────────────────────────────────────
      if (filters.selectivity !== "all") {
        const allowed = SELECTIVITY_MAP[filters.selectivity];
        if (!allowed.includes(p.target_school_selectivity)) return false;
      }

      // ── Mode filter (multi-select — both can be active simultaneously) ──────
      if (filters.mode.includes("apprenticeship")) {
        if (!p.target_school_apprenticeship) return false;
      }
      if (filters.mode.includes("internship")) {
        if (!p.target_school_internship) return false;
      }

      // proximity filter is handled server-side; client sees already-filtered
      // or all results depending on API response (no-op here for proximity).

      return true;
    });
  }, [parcoursList, filters]);
}
