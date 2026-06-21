"use client";

import { type KeyboardEvent } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ParcoursFilters {
  proximity: "all" | "50km" | "200km";
  cost: "all" | "free" | "under5k" | "under10k";
  selectivity: "all" | "open" | "accessible" | "selective" | "very_selective";
  mode: string[];
}

export const DEFAULT_FILTERS: ParcoursFilters = {
  proximity: "all",
  cost: "all",
  selectivity: "all",
  mode: [],
};

// ─── FilterPill ───────────────────────────────────────────────────────────────

interface FilterPillProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

function FilterPill({ label, active, onClick }: FilterPillProps) {
  function handleKeyDown(e: KeyboardEvent<HTMLButtonElement>) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  }

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={active}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={[
        "inline-flex items-center rounded-full px-3 py-1 text-sm font-medium transition-colors",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
        active ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

// ─── FilterBar ────────────────────────────────────────────────────────────────

export interface FilterBarProps {
  filters: ParcoursFilters;
  onChange: (filters: ParcoursFilters) => void;
  resultCount: number;
}

export function FilterBar({ filters, onChange, resultCount }: FilterBarProps) {
  const hasActiveFilters =
    filters.proximity !== "all" ||
    filters.cost !== "all" ||
    filters.selectivity !== "all" ||
    filters.mode.length > 0;

  // ─── Handlers ───────────────────────────────────────────────────────────────

  function setProximity(value: ParcoursFilters["proximity"]) {
    onChange({
      ...filters,
      proximity: filters.proximity === value ? "all" : value,
    });
  }

  function setCost(value: ParcoursFilters["cost"]) {
    onChange({
      ...filters,
      cost: filters.cost === value ? "all" : value,
    });
  }

  function setSelectivity(value: ParcoursFilters["selectivity"]) {
    onChange({
      ...filters,
      selectivity: filters.selectivity === value ? "all" : value,
    });
  }

  function toggleMode(value: string) {
    const current = filters.mode;
    const next = current.includes(value) ? current.filter((m) => m !== value) : [...current, value];
    onChange({ ...filters, mode: next });
  }

  function clearAll() {
    onChange(DEFAULT_FILTERS);
  }

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-3" data-testid="filter-bar">
      {/* Filter groups row */}
      <div className="flex flex-wrap gap-4">
        {/* Proximite */}
        <div role="group" aria-label="Proximite" className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Proximite
          </span>
          <FilterPill
            label="France entiere"
            active={filters.proximity === "all"}
            onClick={() => onChange({ ...filters, proximity: "all" })}
          />
          <FilterPill
            label="<= 50 km"
            active={filters.proximity === "50km"}
            onClick={() => setProximity("50km")}
          />
          <FilterPill
            label="<= 200 km"
            active={filters.proximity === "200km"}
            onClick={() => setProximity("200km")}
          />
        </div>

        {/* Cout */}
        <div role="group" aria-label="Cout" className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Cout</span>
          <FilterPill
            label="Sans limite"
            active={filters.cost === "all"}
            onClick={() => onChange({ ...filters, cost: "all" })}
          />
          <FilterPill
            label="Gratuit"
            active={filters.cost === "free"}
            onClick={() => setCost("free")}
          />
          <FilterPill
            label="< 5 000 euros/an"
            active={filters.cost === "under5k"}
            onClick={() => setCost("under5k")}
          />
          <FilterPill
            label="< 10 000 euros/an"
            active={filters.cost === "under10k"}
            onClick={() => setCost("under10k")}
          />
        </div>

        {/* Selectivite */}
        <div role="group" aria-label="Selectivite" className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Selectivite
          </span>
          <FilterPill
            label="Toutes"
            active={filters.selectivity === "all"}
            onClick={() => onChange({ ...filters, selectivity: "all" })}
          />
          <FilterPill
            label="Tres accessible"
            active={filters.selectivity === "open"}
            onClick={() => setSelectivity("open")}
          />
          <FilterPill
            label="Accessible"
            active={filters.selectivity === "accessible"}
            onClick={() => setSelectivity("accessible")}
          />
          <FilterPill
            label="Selectif"
            active={filters.selectivity === "selective"}
            onClick={() => setSelectivity("selective")}
          />
          <FilterPill
            label="Tres selectif"
            active={filters.selectivity === "very_selective"}
            onClick={() => setSelectivity("very_selective")}
          />
        </div>

        {/* Mode */}
        <div role="group" aria-label="Mode" className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Mode</span>
          <FilterPill
            label="Alternance"
            active={filters.mode.includes("apprenticeship")}
            onClick={() => toggleMode("apprenticeship")}
          />
          <FilterPill
            label="Internat"
            active={filters.mode.includes("internship")}
            onClick={() => toggleMode("internship")}
          />
        </div>
      </div>

      {/* Footer row: result count + clear */}
      <div className="flex items-center justify-between">
        <p aria-live="polite" className="text-sm text-gray-600" data-testid="result-count">
          {resultCount} ecole(s) cible(s) correspondent a tes filtres
        </p>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearAll}
            className="text-sm font-medium text-blue-600 hover:text-blue-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            data-testid="clear-all-btn"
          >
            Effacer tout
          </button>
        )}
      </div>
    </div>
  );
}
