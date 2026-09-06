/**
 * `/[niveau]/quel-bac-pour-[metier]` page tests — Story 7.3.
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

import QuelBacPourMetierPage from "./page";

const PROFESSION = {
  slug: "technicien-aero-test",
  name: "Technicien·ne aéronautique",
  description: "Description du métier.",
  daily_routine: "Routine.",
  requirements_json: [],
  prospects_text: "Chef d'équipe.",
  median_salary_eur: 28000,
  signals_json: { passions: [], valeurs: [], specialites: [] },
  level_compatibility: ["lycee_pro"],
  sector: "aéronautique",
};

describe("QuelBacPourMetierPage", () => {
  beforeEach(() => {
    fetchPublicProfessionMock.mockReset();
    fetchPublicParcoursSummaryMock.mockReset();
    notFoundMock.mockReset();
  });

  it("renders niveau-adapted content with lycées pro for '3eme'", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);
    fetchPublicParcoursSummaryMock.mockResolvedValue([
      {
        niveau_scolaire: "troisieme_bac_pro",
        label: "3ème → Bac Pro Aéronautique",
        is_default: true,
        target_school_name: "Lycée Pro Aéro",
        target_school_slug: "lycee-pro-aero",
        target_school_city: "Toulouse",
      },
    ]);

    render(
      await QuelBacPourMetierPage({
        params: Promise.resolve({
          slug: "3eme",
          metierSlug: "quel-bac-pour-technicien-aero-test",
        }),
      }),
    );

    expect(screen.getByText("Lycées professionnels associés")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Lycée Pro Aéro" })).toHaveAttribute(
      "href",
      "/formations/lycee-pro-aero",
    );
    expect(fetchPublicParcoursSummaryMock).toHaveBeenCalledWith(
      "technicien-aero-test",
      "troisieme_bac_pro",
    );
  });

  it("calls notFound() for an unsupported niveau slug", async () => {
    await QuelBacPourMetierPage({
      params: Promise.resolve({
        slug: "premiere",
        metierSlug: "quel-bac-pour-technicien-aero-test",
      }),
    });

    expect(notFoundMock).toHaveBeenCalled();
    expect(fetchPublicProfessionMock).not.toHaveBeenCalled();
  });

  it("calls notFound() on a 404 (unknown métier)", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await QuelBacPourMetierPage({
      params: Promise.resolve({ slug: "3eme", metierSlug: "quel-bac-pour-metier-inexistant" }),
    });

    expect(notFoundMock).toHaveBeenCalled();
  });

  it("calls notFound() when metierSlug doesn't have the 'quel-bac-pour-' prefix", async () => {
    await QuelBacPourMetierPage({
      params: Promise.resolve({ slug: "3eme", metierSlug: "technicien-aero-test" }),
    });

    expect(notFoundMock).toHaveBeenCalled();
    expect(fetchPublicProfessionMock).not.toHaveBeenCalled();
  });
});
