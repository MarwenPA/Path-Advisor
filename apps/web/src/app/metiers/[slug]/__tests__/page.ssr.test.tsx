/**
 * `/metiers/[slug]` server-HTML guarantee — Story 7.9.
 *
 * Story 7.6/7.9 lesson: the unit tests were green while the prerendered
 * HTML was an EMPTY SHELL (`<Suspense fallback={null}>` around a
 * `useSearchParams` body), because jsdom rendering hydrates everything and
 * hides the difference. This test renders the page's actual returned tree
 * through `renderToString` — the same server-rendering pass `next build`
 * uses — with NO mock for the fiche components and NO mock for
 * `next/navigation`. It fails in two ways the old structure would have
 * tripped:
 *
 * - a `useSearchParams()` call anywhere in the tree throws outside a Next
 *   router context (and, in the real build, forces the Suspense fallback);
 * - content hidden behind a `fallback={null}` boundary would simply be
 *   absent from the string.
 *
 * So a green run here means: the LCP content (title, description,
 * sections, signup CTA) is in the server HTML, with no client boundary
 * swallowing it, and no score/personalization frozen into the cacheable
 * HTML.
 */
import { NextIntlClientProvider } from "next-intl";
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

import MetierDetailPage from "../page";

const PROFESSION = {
  slug: "technicien-aeronautique",
  name: "Technicien aéronautique",
  description: "Le technicien aéronautique assure la maintenance des aéronefs.",
  daily_routine: "Inspections, diagnostics et réparations au hangar.",
  requirements_json: [{ type: "studies", label: "Bac pro aéronautique" }],
  prospects_text: "Compagnies aériennes, ateliers de maintenance.",
  median_salary_eur: 30000,
  signals_json: { passions: ["Mécanique"], valeurs: [], specialites: [] },
  level_compatibility: ["bac_pro"],
  sector: "aéronautique",
};

describe("MetierDetailPage — prerendered HTML (Story 7.9 AC1)", () => {
  it("server-renders the full anonymous fiche: LCP content present, no personalization", async () => {
    fetchPublicProfessionMock.mockResolvedValue(PROFESSION);

    const tree = await MetierDetailPage({
      params: Promise.resolve({ slug: "technicien-aeronautique" }),
    });

    const html = renderToString(
      <NextIntlClientProvider locale="fr" messages={messages}>
        {tree}
      </NextIntlClientProvider>,
    );

    // The LCP element (`<p class="text-body text-text">` with the
    // description) must be in the server HTML — this is exactly the string
    // that was missing from the `curl` output before the fix.
    expect(html).toContain("Le technicien aéronautique assure la maintenance des aéronefs.");
    expect(html).toContain("text-body text-text");
    // Title + the other main sections.
    expect(html).toContain("Technicien aéronautique");
    expect(html).toContain("Journée type");
    expect(html).toContain("Compagnies aériennes, ateliers de maintenance.");
    expect(html).toContain("30");
    // Anonymous variant: signup CTA present, back-to-list link present.
    expect(html).toContain(messages.metierPage.signupCtaTitle);
    expect(html).toContain(messages.metierPage.backToList);
    // No personalization may ever be baked into the cacheable HTML.
    expect(html).not.toContain("/mes-metiers");
    expect(html).not.toMatch(/Score\s*:/);
  });
});
