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

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

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

  it("links to the four /{niveau}/quel-bac-pour-{metier} pages (Epic 7 review — orphan fix)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);
    fetchPublicParcoursSummaryMock.mockResolvedValue([]);

    render(
      await DevenirMetierPage({ params: Promise.resolve({ slug: "devenir-infirmier-test" }) }),
    );

    for (const niveau of [
      "3eme",
      "terminale-generale",
      "terminale-technologique",
      "terminale-pro",
    ]) {
      expect(
        document.querySelector(`a[href="/${niveau}/quel-bac-pour-infirmier-test"]`),
      ).not.toBeNull();
    }
  });

  it("escapes </script> in JSON-LD (Epic 7 review — stored XSS)", async () => {
    fetchPublicProfessionMock.mockResolvedValue({
      ...PROFESSION,
      prospects_text: `piégé</script><script>alert("xss")</script>`,
    });
    fetchPublicParcoursSummaryMock.mockResolvedValue([]);

    const { container } = render(
      await DevenirMetierPage({ params: Promise.resolve({ slug: "devenir-infirmier-test" }) }),
    );

    for (const script of container.querySelectorAll('script[type="application/ld+json"]')) {
      expect(script.innerHTML).not.toContain("</script>");
    }
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
