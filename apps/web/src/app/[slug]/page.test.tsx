/**
 * `/devenir-[metier]` page tests — Story 7.3.
 */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

const fetchPublicParcoursSummaryMock = vi.fn();
vi.mock("@/lib/api/schools", () => ({
  fetchPublicParcoursSummary: (...args: unknown[]) => fetchPublicParcoursSummaryMock(...args),
}));

const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

import { ApiError } from "@/lib/api/client";

import DevenirMetierPage from "./page";

const PROFESSION = {
  slug: "infirmier-test",
  name: "Infirmier·ère",
  description: "Description du métier.",
  daily_routine: "Routine.",
  requirements_json: [{ type: "studies", label: "DEI 3 ans" }],
  prospects_text: "Cadre de santé.",
  median_salary_eur: 32000,
  signals_json: { passions: [], valeurs: [], specialites: [] },
  level_compatibility: ["lycee_1ere_tle_general"],
  sector: "santé",
};

describe("DevenirMetierPage", () => {
  beforeEach(() => {
    fetchPublicProfessionMock.mockReset();
    fetchPublicParcoursSummaryMock.mockReset();
    notFoundMock.mockReset();
  });

  it("renders the fiche, FAQ, quels-bacs panel and signup CTA", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);
    fetchPublicParcoursSummaryMock.mockResolvedValue([
      {
        niveau_scolaire: "terminale_generale",
        label: "Bac général → IFSI",
        is_default: true,
        target_school_name: "IFSI Paris",
        target_school_slug: "ifsi-paris",
        target_school_city: "Paris",
      },
    ]);

    render(
      await DevenirMetierPage({ params: Promise.resolve({ slug: "devenir-infirmier-test" }) }),
    );

    expect(screen.getByRole("heading", { name: /devenir infirmier/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "IFSI Paris" })).toHaveAttribute(
      "href",
      "/formations/ifsi-paris",
    );
    expect(screen.getByText(/quel est le salaire/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /créer mon compte/i })).toBeInTheDocument();
    expect(fetchPublicProfessionMock).toHaveBeenCalledWith("infirmier-test");
  });

  it("calls notFound() on a 404 (unknown métier)", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await DevenirMetierPage({ params: Promise.resolve({ slug: "devenir-metier-inexistant" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });

  it("calls notFound() when the slug doesn't have the 'devenir-' prefix", async () => {
    await DevenirMetierPage({ params: Promise.resolve({ slug: "infirmier-test" }) });

    expect(notFoundMock).toHaveBeenCalled();
    expect(fetchPublicProfessionMock).not.toHaveBeenCalled();
  });

  it("still renders when the parcours summary fetch fails", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);
    fetchPublicParcoursSummaryMock.mockRejectedValue(new Error("network"));

    render(
      await DevenirMetierPage({ params: Promise.resolve({ slug: "devenir-infirmier-test" }) }),
    );

    expect(screen.getByRole("heading", { name: /devenir infirmier/i })).toBeInTheDocument();
  });
});
