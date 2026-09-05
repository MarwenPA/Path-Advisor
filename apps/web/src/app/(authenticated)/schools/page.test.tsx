/**
 * `/schools` catalogue page tests — mirrors `/metiers`'s (Story 3.13).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchSchoolsMock = vi.fn();
vi.mock("@/lib/api/schools", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/schools")>("@/lib/api/schools");
  return {
    ...actual,
    fetchSchools: () => fetchSchoolsMock(),
  };
});

import SchoolsCataloguePage from "./page";

function makeCatalogItem(overrides = {}) {
  return {
    id: "school_01",
    slug: "ifsi-paris",
    name: "IFSI Paris",
    type: "ecole_sante",
    city: "Paris",
    region: "Île-de-France",
    selectivity_index: 3,
    ...overrides,
  };
}

describe("SchoolsCataloguePage", () => {
  it("renders one card per school, linking to its detail page", async () => {
    fetchSchoolsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [makeCatalogItem()],
    });

    render(await SchoolsCataloguePage());

    expect(screen.getByText("IFSI Paris")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ifsi paris/i })).toHaveAttribute(
      "href",
      "/schools/ifsi-paris",
    );
  });

  it("shows the type, city, region and selectivity", async () => {
    fetchSchoolsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        makeCatalogItem({
          type: "ecole_ingenieur",
          city: "Lyon",
          region: "Auvergne-Rhône-Alpes",
          selectivity_index: 1,
        }),
      ],
    });

    render(await SchoolsCataloguePage());

    expect(screen.getByText(/ecole_ingenieur · Lyon/)).toBeInTheDocument();
    expect(screen.getByText(/Sélectivité 1\/5 — Auvergne-Rhône-Alpes/)).toBeInTheDocument();
  });

  it("shows the total count of schools", async () => {
    fetchSchoolsMock.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [makeCatalogItem(), makeCatalogItem({ id: "school_02", slug: "autre-ecole" })],
    });

    render(await SchoolsCataloguePage());

    expect(screen.getByText(/2 établissements à explorer/i)).toBeInTheDocument();
  });
});
