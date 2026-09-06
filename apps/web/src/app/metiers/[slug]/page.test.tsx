/**
 * `/metiers/[slug]` page tests — Story 7.1 (public SSR fiche métier).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

vi.mock("./FicheMetierClient", () => ({
  FicheMetierClient: ({ profession }: { profession: { name: string } }) => (
    <div data-testid="fiche-metier-client">{profession.name}</div>
  ),
}));

import { ApiError } from "@/lib/api/client";

import MetierDetailPage, { generateMetadata } from "./page";

const PROFESSION = {
  slug: "infirmier-test",
  name: "Infirmier·ère",
  description: "Description longue du métier d'infirmier.",
  daily_routine: "Une journée type.",
  requirements_json: [],
  prospects_text: "Débouchés.",
  median_salary_eur: 32000,
  signals_json: { passions: [], valeurs: [], specialites: [] },
  level_compatibility: [],
  sector: "santé",
};

describe("MetierDetailPage (public)", () => {
  it("renders the CTA to sign up for an anonymous visit (no score in query)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    render(
      await MetierDetailPage({
        params: Promise.resolve({ slug: "infirmier-test" }),
        searchParams: Promise.resolve({}),
      }),
    );

    expect(screen.getByTestId("fiche-metier-client")).toHaveTextContent("Infirmier·ère");
    expect(
      screen.getByRole("link", { name: /crée ton compte pour voir tes chances réelles/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /tous les métiers/i })).toBeInTheDocument();
  });

  it("emits Schema.org Occupation JSON-LD (Story 7.4 AC)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    const { container } = render(
      await MetierDetailPage({
        params: Promise.resolve({ slug: "infirmier-test" }),
        searchParams: Promise.resolve({}),
      }),
    );

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).not.toBeNull();
    const jsonLd = JSON.parse(script!.innerHTML);
    expect(jsonLd["@type"]).toBe("Occupation");
    expect(jsonLd.name).toBe("Infirmier·ère");
  });

  it("exposes og:url/type and a Twitter summary_large_image card (Story 7.5 AC)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    const metadata = await generateMetadata({
      params: Promise.resolve({ slug: "infirmier-test" }),
    });

    expect(metadata.openGraph?.url).toBe("https://path-advisor.fr/metiers/infirmier-test");
    expect(metadata.openGraph?.type).toBe("website");
    expect(metadata.twitter?.card).toBe("summary_large_image");
  });

  it("hides the signup CTA when arriving from the authenticated recommendations flow", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    render(
      await MetierDetailPage({
        params: Promise.resolve({ slug: "infirmier-test" }),
        searchParams: Promise.resolve({ score: "82", confidence: "high" }),
      }),
    );

    expect(
      screen.queryByRole("link", { name: /crée ton compte pour voir tes chances réelles/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /mes métiers/i })).toBeInTheDocument();
  });

  it("calls notFound() on a 404 (unknown slug)", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await MetierDetailPage({
      params: Promise.resolve({ slug: "metier-inexistant" }),
      searchParams: Promise.resolve({}),
    });

    expect(notFoundMock).toHaveBeenCalled();
  });
});
