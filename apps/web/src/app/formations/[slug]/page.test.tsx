/**
 * `/formations/[slug]` page tests — Story 7.2 (public SSR fiche
 * école/formation).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchPublicSchoolMock = vi.fn();
vi.mock("@/lib/api/schools", () => ({
  fetchPublicSchool: (...args: unknown[]) => fetchPublicSchoolMock(...args),
}));

const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

vi.mock("@/components/schools/FicheEcole", () => ({
  FicheEcole: ({ school }: { school: { name: string } }) => (
    <div data-testid="fiche-ecole">{school.name}</div>
  ),
}));

import { ApiError } from "@/lib/api/client";

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

import PublicFormationPage, { generateMetadata } from "./page";

const SCHOOL = {
  slug: "insa-lyon",
  name: "INSA Lyon",
  type: "ecole_ingenieur",
  city: "Lyon",
  region: "Auvergne-Rhône-Alpes",
  postal_code: "69100",
  apprenticeship: false,
  internship: true,
  selectivity_index: 2,
  public_private: "public",
  description: "École d'ingénieurs généraliste.",
  top_debouches: ["Ingénieur"],
  parcoursup_dates: {},
  affelnet_dates: {},
  official_url: "https://insa-lyon.fr",
  formations: [],
  metiers_cibles: [{ slug: "ingenieur-test", name: "Ingénieur" }],
  similar_schools: [{ slug: "autre-ecole", name: "Autre École", city: "Paris" }],
};

describe("PublicFormationPage", () => {
  it("renders the fiche + cross-links + signup CTA", async () => {
    fetchPublicSchoolMock.mockResolvedValue(SCHOOL);

    render(await PublicFormationPage({ params: Promise.resolve({ slug: "insa-lyon" }) }));

    expect(screen.getByTestId("fiche-ecole")).toHaveTextContent("INSA Lyon");
    expect(screen.getByRole("link", { name: "Ingénieur" })).toHaveAttribute(
      "href",
      "/metiers/ingenieur-test",
    );
    expect(screen.getByRole("link", { name: "Autre École" })).toHaveAttribute(
      "href",
      "/formations/autre-ecole",
    );
    expect(
      screen.getByRole("link", {
        name: /crée ton compte pour voir ta proba d'admission personnalisée/i,
      }),
    ).toBeInTheDocument();
  });

  it("emits Schema.org EducationalOrganization JSON-LD (Story 7.4 AC)", async () => {
    fetchPublicSchoolMock.mockResolvedValue(SCHOOL);

    const { container } = render(
      await PublicFormationPage({ params: Promise.resolve({ slug: "insa-lyon" }) }),
    );

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).not.toBeNull();
    const jsonLd = JSON.parse(script!.innerHTML);
    expect(jsonLd["@type"]).toBe("EducationalOrganization");
    expect(jsonLd.name).toBe("INSA Lyon");
  });

  it("omits the cross-linking sections when empty", async () => {
    fetchPublicSchoolMock.mockResolvedValue({
      ...SCHOOL,
      metiers_cibles: [],
      similar_schools: [],
    });

    render(await PublicFormationPage({ params: Promise.resolve({ slug: "insa-lyon" }) }));

    expect(screen.queryByText("Métiers auxquels cette formation mène")).not.toBeInTheDocument();
    expect(screen.queryByText("Écoles similaires")).not.toBeInTheDocument();
  });

  it("calls notFound() on a 404 (unknown slug)", async () => {
    fetchPublicSchoolMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await PublicFormationPage({ params: Promise.resolve({ slug: "ecole-inexistante" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });
});

describe("generateMetadata", () => {
  it("uses the school description when present", async () => {
    fetchPublicSchoolMock.mockResolvedValue(SCHOOL);

    const metadata = await generateMetadata({ params: Promise.resolve({ slug: "insa-lyon" }) });

    expect(metadata.description).toBe("École d'ingénieurs généraliste.");
  });

  it("falls back to a generic description when the school has none (Story 7.6 SEO fix)", async () => {
    fetchPublicSchoolMock.mockResolvedValue({ ...SCHOOL, description: "" });

    const metadata = await generateMetadata({ params: Promise.resolve({ slug: "insa-lyon" }) });

    expect(metadata.description).toBeTruthy();
    expect(metadata.description).toContain("INSA Lyon");
    expect(metadata.description).toContain("Lyon");
  });
});
