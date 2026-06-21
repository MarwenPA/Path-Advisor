"use client";

import { useState } from "react";

import { DEFAULT_FILTERS, FilterBar } from "./FilterBar";
import type { ParcoursFilters } from "./FilterBar";
import { useParcoursFilters } from "./useParcoursFilters";
import type { Parcours } from "./types";

// ─── Props ────────────────────────────────────────────────────────────────────

interface ParcoursListClientProps {
  parcoursList: Parcours[];
}

// ─── Empty state ──────────────────────────────────────────────────────────────

interface ParcoursEmptyStateProps {
  onRelaxFilter: () => void;
}

function ParcoursEmptyState({ onRelaxFilter }: ParcoursEmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-gray-300 p-10 text-center"
      data-testid="parcours-empty-state"
    >
      <p className="text-base font-medium text-gray-700">
        Aucune ecole ne correspond. Elargis tes criteres ?
      </p>
      <button
        type="button"
        onClick={onRelaxFilter}
        className="inline-flex items-center rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        data-testid="relax-filter-btn"
      >
        Relacher un filtre
      </button>
    </div>
  );
}

// ─── ParcoursListClient ───────────────────────────────────────────────────────

/**
 * Client wrapper that owns filter state, runs useParcoursFilters,
 * and renders FilterBar + ParcoursList (or empty state).
 *
 * Story 4.6 — server component passes the full parcours array;
 * filtering is done client-side so there is no additional network roundtrip.
 */
export function ParcoursListClient({ parcoursList }: ParcoursListClientProps) {
  const [filters, setFilters] = useState<ParcoursFilters>(DEFAULT_FILTERS);
  const filtered = useParcoursFilters(parcoursList, filters);

  function handleRelaxFilter() {
    setFilters(DEFAULT_FILTERS);
  }

  return (
    <div className="flex flex-col gap-6" data-testid="parcours-list-client">
      <FilterBar filters={filters} onChange={setFilters} resultCount={filtered.length} />

      {filtered.length === 0 ? (
        <ParcoursEmptyState onRelaxFilter={handleRelaxFilter} />
      ) : (
        <ul className="flex flex-col gap-4" aria-label="Parcours correspondants">
          {filtered.map((p) => (
            <li key={p.id} className="rounded-xl border border-gray-200 p-4 shadow-sm">
              <span className="font-semibold text-gray-800">{p.target_school_name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
