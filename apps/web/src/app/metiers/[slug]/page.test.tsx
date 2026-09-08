/**
 * `/metiers/[slug]` page tests — Story 7.1 (public SSR fiche métier).
 *
 * Epic 7 review: the query-param-dependent UI moved to `MetierPageBody`
 * so the Server Component stays ISR-cacheable. Story 7.9: the body reads
 * `window.location.search` (not `useSearchParams`, which forced an empty
 * Suspense-fallback shell on prerender), so the two arrival flows are
 * simulated with `history.replaceState` on jsdom's real location. Rendering
 * goes through `renderWithIntl` (the body uses `useTranslations`).
 *
 * See `__tests__/page.ssr.test.tsx` for the server-HTML guarantee itself.
 */
import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderWithIntl } from "@/test/render-with-intl";

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

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

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
  beforeEach(() => {
    // Story 7.9 — the body reads window.location.search; reset the URL to
    // an anonymous visit before each test.
    window.history.replaceState({}, "", "/metiers/infirmier-test");
  });

  it("renders the CTA to sign up for an anonymous visit (no score in query)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    renderWithIntl(
      (await MetierDetailPage({ params: Promise.resolve({ slug: "infirmier-test" }) }))!,
    );

    expect(screen.getByTestId("fiche-metier-client")).toHaveTextContent("Infirmier·ère");
    expect(
      screen.getByRole("link", { name: /crée ton compte pour voir tes chances réelles/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /tous les métiers/i })).toBeInTheDocument();
  });

  it("emits Schema.org Occupation JSON-LD (Story 7.4 AC)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    const { container } = renderWithIntl(
      (await MetierDetailPage({ params: Promise.resolve({ slug: "infirmier-test" }) }))!,
    );

    const script = container.querySelector('script[type="application/ld+json"]');
    expect(script).not.toBeNull();
    const jsonLd = JSON.parse(script!.innerHTML);
    expect(jsonLd["@type"]).toBe("Occupation");
    expect(jsonLd.name).toBe("Infirmier·ère");
  });

  it("escapes </script> in JSON-LD (Epic 7 review — stored XSS)", async () => {
    fetchPublicProfessionMock.mockResolvedValue({
      ...PROFESSION,
      description: `piégé</script><script>alert("xss")</script>`,
    });

    const { container } = renderWithIntl(
      (await MetierDetailPage({ params: Promise.resolve({ slug: "infirmier-test" }) }))!,
    );

    // Exactly ONE script element must exist — a breakout payload would
    // have split it into several plus live markup.
    const scripts = container.querySelectorAll("script");
    expect(scripts).toHaveLength(1);
    expect(scripts[0]!.innerHTML).not.toContain("</script>");
    // The escaped JSON still round-trips to the raw payload.
    expect(JSON.parse(scripts[0]!.innerHTML).description).toContain("</script>");
  });

  it("exposes og:url/type, a canonical URL and a Twitter summary_large_image card (Stories 7.4/7.5)", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    const metadata = await generateMetadata({
      params: Promise.resolve({ slug: "infirmier-test" }),
    });

    expect(metadata.openGraph?.url).toBe("https://path-advisor.fr/metiers/infirmier-test");
    expect(metadata.openGraph?.type).toBe("website");
    expect(metadata.twitter?.card).toBe("summary_large_image");
    // Epic 7 review fix — canonical strips the ?score= personalization
    // params (relative path, resolved against the layout's metadataBase).
    expect(metadata.alternates?.canonical).toBe("/metiers/infirmier-test");
  });

  it("hides the signup CTA when arriving from the authenticated recommendations flow", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);
    window.history.replaceState({}, "", "/metiers/infirmier-test?score=82&confidence=high");

    renderWithIntl(
      (await MetierDetailPage({ params: Promise.resolve({ slug: "infirmier-test" }) }))!,
    );

    expect(
      screen.queryByRole("link", { name: /crée ton compte pour voir tes chances réelles/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /mes métiers/i })).toBeInTheDocument();
  });

  it("calls notFound() on a 404 (unknown slug)", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await MetierDetailPage({ params: Promise.resolve({ slug: "metier-inexistant" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });

  it("falls back to a generic description when the profession has none (Story 7.6 SEO fix)", async () => {
    fetchPublicProfessionMock.mockResolvedValue({ ...PROFESSION, description: "" });

    const metadata = await generateMetadata({
      params: Promise.resolve({ slug: "infirmier-test" }),
    });

    expect(metadata.description).toBeTruthy();
    expect(metadata.description).toContain("Infirmier·ère");
  });
});
