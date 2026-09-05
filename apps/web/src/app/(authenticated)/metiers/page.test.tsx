/**
 * `/metiers` catalogue page tests — Story 3.13.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchProfessionsMock = vi.fn();
vi.mock("@/lib/api/professions", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/api/professions")>("@/lib/api/professions");
  return {
    ...actual,
    fetchProfessions: () => fetchProfessionsMock(),
  };
});

import MetiersCataloguePage from "./page";

function makeCatalogItem(overrides = {}) {
  return {
    id: "prof_01",
    slug: "infirmier-ssr",
    name: "Infirmier·ère SSR",
    description: "Prend en charge des patients en soins de suite.",
    sector: "santé",
    median_salary_eur: 28000,
    ...overrides,
  };
}

describe("MetiersCataloguePage", () => {
  it("renders one card per profession, linking to its detail page", async () => {
    fetchProfessionsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [makeCatalogItem()],
    });

    render(await MetiersCataloguePage());

    expect(screen.getByText("Infirmier·ère SSR")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /infirmier·ère ssr/i })).toHaveAttribute(
      "href",
      "/metiers/infirmier-ssr",
    );
  });

  it("shows the sector and formatted median salary when present", async () => {
    fetchProfessionsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [makeCatalogItem({ sector: "tech", median_salary_eur: 45000 })],
    });

    render(await MetiersCataloguePage());

    expect(screen.getByText("tech")).toBeInTheDocument();
    expect(screen.getByText(/45\s?000\s?€ \/ an/)).toBeInTheDocument();
  });

  it("does not crash when sector/median_salary_eur are absent", async () => {
    fetchProfessionsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [makeCatalogItem({ sector: undefined, median_salary_eur: null })],
    });

    render(await MetiersCataloguePage());

    expect(screen.getByText("Infirmier·ère SSR")).toBeInTheDocument();
  });

  it("shows the total count of professions", async () => {
    fetchProfessionsMock.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [makeCatalogItem(), makeCatalogItem({ id: "prof_02", slug: "autre-metier" })],
    });

    render(await MetiersCataloguePage());

    expect(screen.getByText(/2 métiers à explorer/i)).toBeInTheDocument();
  });
});
