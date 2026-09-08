/**
 * `/formations/[slug]` server-HTML guarantee — Story 7.9 AC1.
 *
 * Same rationale as `/metiers/[slug]/__tests__/page.ssr.test.tsx`: render
 * the page's actual returned tree through `renderToString` (the pass
 * `next build` uses) with the REAL `FicheEcole` (no component mock, no
 * `next/navigation` mock) and assert the fiche's content is in the server
 * HTML — a client boundary swallowing it, or a `useSearchParams` call
 * sneaking into the tree, fails this test.
 */
import { NextIntlClientProvider } from "next-intl";
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import messages from "../../../../messages/fr.json";

const fetchPublicSchoolMock = vi.fn();
vi.mock("@/lib/api/schools", () => ({
  fetchPublicSchool: (...args: unknown[]) => fetchPublicSchoolMock(...args),
}));

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

import PublicFormationPage from "./page";

const SCHOOL = {
  slug: "lycee-pro-aviation",
  name: "Lycée pro aviation",
  type: "lycee_pro",
  city: "Toulouse",
  region: "Occitanie",
  postal_code: "31000",
  apprenticeship: true,
  internship: true,
  selectivity_index: 2,
  public_private: "public",
  description: "Formation aux métiers de l'aéronautique dès le lycée.",
  top_debouches: ["Technicien aéronautique"],
  parcoursup_dates: {},
  affelnet_dates: {},
  official_url: "https://exemple.fr",
  formations: [],
  metiers_cibles: [{ slug: "technicien-aeronautique", name: "Technicien aéronautique" }],
  similar_schools: [],
};

describe("PublicFormationPage — prerendered HTML (Story 7.9 AC1)", () => {
  it("server-renders the full fiche école content", async () => {
    fetchPublicSchoolMock.mockResolvedValue(SCHOOL);

    const tree = await PublicFormationPage({
      params: Promise.resolve({ slug: "lycee-pro-aviation" }),
    });

    const html = renderToString(
      <NextIntlClientProvider locale="fr" messages={messages}>
        {tree}
      </NextIntlClientProvider>,
    );

    // Note: FicheEcole renders no free-text description block — the fiche's
    // visible content is the heading, location, facts grid and débouchés.
    expect(html).toContain("Lycée pro aviation");
    expect(html).toContain("Toulouse");
    expect(html).toContain("Technicien aéronautique");
    // renderToString HTML-escapes apostrophes (&#x27;).
    expect(html).toContain(messages.formationPage.signupCtaTitle.replaceAll("'", "&#x27;"));
    expect(html).toContain(messages.formationPage.targetMetiersTitle.replaceAll("'", "&#x27;"));
  });
});
