import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { FilterBar, DEFAULT_FILTERS } from "../FilterBar";
import type { ParcoursFilters } from "../FilterBar";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function renderFilterBar(
  overrides: Partial<{
    filters: ParcoursFilters;
    resultCount: number;
    onChange: (f: ParcoursFilters) => void;
  }> = {},
) {
  const onChange = overrides.onChange ?? vi.fn();
  const filters = overrides.filters ?? DEFAULT_FILTERS;
  const resultCount = overrides.resultCount ?? 12;

  const utils = render(
    <FilterBar filters={filters} onChange={onChange} resultCount={resultCount} />,
  );
  return { ...utils, onChange };
}

// ─── Group roles + aria-labels ────────────────────────────────────────────────

describe("FilterBar — group roles", () => {
  it("has role=group and aria-label for all 4 groups", () => {
    renderFilterBar();

    expect(screen.getByRole("group", { name: "Proximite" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Cout" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Selectivite" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Mode" })).toBeInTheDocument();
  });
});

// ─── Pill role=checkbox ───────────────────────────────────────────────────────

describe("FilterBar — pills", () => {
  it("pills have role=checkbox", () => {
    renderFilterBar();
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThan(0);
  });

  it("default pills have aria-checked=false for non-default values", () => {
    renderFilterBar();
    // "Gratuit" is not active by default
    const gratuitPill = screen.getByRole("checkbox", { name: "Gratuit" });
    expect(gratuitPill).toHaveAttribute("aria-checked", "false");
  });

  it("default 'France entiere' pill has aria-checked=true", () => {
    renderFilterBar();
    const francePill = screen.getByRole("checkbox", { name: "France entiere" });
    expect(francePill).toHaveAttribute("aria-checked", "true");
  });

  it("clicking an inactive pill calls onChange with new filter active", () => {
    const { onChange } = renderFilterBar();
    const gratuitPill = screen.getByRole("checkbox", { name: "Gratuit" });
    fireEvent.click(gratuitPill);
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ cost: "free" }));
  });

  it("clicking an active pill toggles it off (back to 'all')", () => {
    const { onChange } = renderFilterBar({
      filters: { ...DEFAULT_FILTERS, cost: "free" },
    });
    const gratuitPill = screen.getByRole("checkbox", { name: "Gratuit" });
    expect(gratuitPill).toHaveAttribute("aria-checked", "true");
    fireEvent.click(gratuitPill);
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ cost: "all" }));
  });

  it("pressing Enter on a pill triggers onClick", () => {
    const { onChange } = renderFilterBar();
    const pill = screen.getByRole("checkbox", { name: "Gratuit" });
    fireEvent.keyDown(pill, { key: "Enter" });
    expect(onChange).toHaveBeenCalled();
  });

  it("pressing Space on a pill triggers onClick", () => {
    const { onChange } = renderFilterBar();
    const pill = screen.getByRole("checkbox", { name: "Alternance" });
    fireEvent.keyDown(pill, { key: " " });
    expect(onChange).toHaveBeenCalled();
  });
});

// ─── "Effacer tout" button ────────────────────────────────────────────────────

describe("FilterBar — Effacer tout", () => {
  it("is NOT visible when no filters are active", () => {
    renderFilterBar({ filters: DEFAULT_FILTERS });
    expect(screen.queryByTestId("clear-all-btn")).not.toBeInTheDocument();
  });

  it("IS visible when a filter is active", () => {
    renderFilterBar({ filters: { ...DEFAULT_FILTERS, cost: "free" } });
    expect(screen.getByTestId("clear-all-btn")).toBeInTheDocument();
  });

  it("IS visible when mode filter is active", () => {
    renderFilterBar({ filters: { ...DEFAULT_FILTERS, mode: ["apprenticeship"] } });
    expect(screen.getByTestId("clear-all-btn")).toBeInTheDocument();
  });

  it("clicking 'Effacer tout' calls onChange with DEFAULT_FILTERS", () => {
    const { onChange } = renderFilterBar({
      filters: { ...DEFAULT_FILTERS, cost: "free", selectivity: "selective" },
    });
    const clearBtn = screen.getByTestId("clear-all-btn");
    fireEvent.click(clearBtn);
    expect(onChange).toHaveBeenCalledWith(DEFAULT_FILTERS);
  });
});

// ─── Result count ─────────────────────────────────────────────────────────────

describe("FilterBar — result count", () => {
  it("shows result count text", () => {
    renderFilterBar({ resultCount: 7 });
    expect(screen.getByTestId("result-count")).toHaveTextContent("7");
  });

  it("result count has aria-live=polite", () => {
    renderFilterBar();
    const counter = screen.getByTestId("result-count");
    expect(counter).toHaveAttribute("aria-live", "polite");
  });
});
