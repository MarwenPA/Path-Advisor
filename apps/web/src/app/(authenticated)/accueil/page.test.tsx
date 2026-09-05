/**
 * `/accueil` page tests — Story 8.8 §T4.1.
 *
 * Server Component: awaited directly then rendered, mirroring the pattern in
 * `app/page.test.tsx` — mocks by module (`@/lib/api/recommendations`,
 * `@/lib/api/mes-paris`), never a global `fetch` mock. `ProgressionModule` is
 * mocked as a whole (it is a client component with its own data-fetching
 * lifecycle, covered indirectly here and directly by
 * `profile-maturity-indicator.test.tsx`).
 */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { RecommendationsResponse, ScoredProfession } from "@/lib/api/recommendations";
import type { School } from "@/lib/api/schools";

const fetchRecommendationsMock = vi.fn();
vi.mock("@/lib/api/recommendations", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/recommendations")>(
    "@/lib/api/recommendations",
  );
  return {
    ...actual,
    fetchRecommendations: () => fetchRecommendationsMock(),
  };
});

const fetchMesParisMock = vi.fn();
vi.mock("@/lib/api/mes-paris", () => ({
  fetchMesParis: () => fetchMesParisMock(),
}));

vi.mock("./ProgressionModule", () => ({
  // Mirrors the real component's post-code-review shape: it now owns its
  // own <section>/<h2> (so an empty landmark is never rendered when it
  // returns null — see ProgressionModule.tsx).
  ProgressionModule: () => (
    <section aria-labelledby="accueil-progression-title" data-testid="progression-module">
      <h2 id="accueil-progression-title" className="sr-only">
        Ta progression
      </h2>
    </section>
  ),
}));

vi.mock("@/components/schools/FicheEcole", () => ({
  FicheEcole: ({ school }: { school: School }) => (
    <div data-testid="fiche-ecole">{school.name}</div>
  ),
}));

import AccueilPage from "./page";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeProfession(overrides: Partial<ScoredProfession> = {}): ScoredProfession {
  return {
    id: "prof_01",
    slug: "infirmier",
    name: "Infirmier·ère",
    sector: "santé",
    score: 85,
    confidence_level: "high",
    signals_contributifs: [{ signal: "passion_soins", weight: 0.3, contribution: 25 }],
    phrase_recopiable: "",
    ...overrides,
  };
}

function makeSchool(overrides: Partial<School> = {}): School {
  return {
    id: "school_01",
    slug: "ifsi-paris",
    name: "IFSI Paris",
    type: "IFSI",
    city: "Paris",
    region: "Île-de-France",
    postal_code: "75001",
    apprenticeship: false,
    internship: true,
    selectivity_index: 3,
    public_private: "public",
    description: "",
    top_debouches: [],
    parcoursup_dates: {},
    affelnet_dates: {},
    official_url: "",
    formations: [],
    ...overrides,
  };
}

function makeRecoResponse(results: ScoredProfession[]): RecommendationsResponse {
  return { results, computed_at: new Date().toISOString() };
}

beforeEach(() => {
  fetchRecommendationsMock.mockReset();
  fetchMesParisMock.mockReset();
});

describe("AccueilPage", () => {
  it("renders 3 sections in order: progression, métiers, paris", async () => {
    fetchRecommendationsMock.mockResolvedValue(makeRecoResponse([makeProfession()]));
    fetchMesParisMock.mockResolvedValue([makeSchool()]);

    render(await AccueilPage());

    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings.map((h) => h.textContent)).toEqual([
      "Ta progression",
      "Tes métiers",
      "Tes paris",
    ]);
    expect(screen.getByTestId("progression-module")).toBeInTheDocument();
  });

  it("shows the top-3 recommendations sorted by score desc, each linking to its fiche métier", async () => {
    fetchRecommendationsMock.mockResolvedValue(
      makeRecoResponse([
        makeProfession({ id: "p1", slug: "low", name: "Low", score: 10 }),
        makeProfession({ id: "p2", slug: "high", name: "High", score: 95 }),
        makeProfession({ id: "p3", slug: "mid", name: "Mid", score: 50 }),
        makeProfession({ id: "p4", slug: "extra", name: "Extra", score: 40 }),
      ]),
    );
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    const list = screen.getByTestId("accueil-metiers-list");
    const items = list.querySelectorAll("li");
    expect(items).toHaveLength(3);
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Mid")).toBeInTheDocument();
    expect(screen.queryByText("Low")).not.toBeInTheDocument();

    const link = screen.getByRole("link", { name: /High/ });
    expect(link.getAttribute("href")).toMatch(
      /^\/metiers\/high\?score=95&confidence=high&signals=/,
    );

    expect(screen.getByRole("link", { name: "Voir tous mes métiers" })).toHaveAttribute(
      "href",
      "/mes-metiers",
    );
  });

  it("shows the top-3 mes-paris schools with a link to /mes-paris", async () => {
    fetchRecommendationsMock.mockResolvedValue(makeRecoResponse([]));
    fetchMesParisMock.mockResolvedValue([
      makeSchool({ id: "s1", name: "École A" }),
      makeSchool({ id: "s2", name: "École B" }),
      makeSchool({ id: "s3", name: "École C" }),
      makeSchool({ id: "s4", name: "École D" }),
    ]);

    render(await AccueilPage());

    const list = screen.getByTestId("accueil-mesparis-list");
    expect(list.querySelectorAll("li")).toHaveLength(3);
    expect(screen.getByText("École A")).toBeInTheDocument();
    expect(screen.queryByText("École D")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voir tous mes paris" })).toHaveAttribute(
      "href",
      "/mes-paris",
    );
  });

  it("shows the métiers empty state when there are no recommendations", async () => {
    fetchRecommendationsMock.mockResolvedValue(makeRecoResponse([]));
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    expect(
      screen.getByText(/Tes recommandations arrivent dès que ton profil est prêt/),
    ).toBeInTheDocument();
  });

  it("Story 3.13 — shows a link to the full catalog when there are no recommendations", async () => {
    fetchRecommendationsMock.mockResolvedValue(makeRecoResponse([]));
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    expect(screen.getByRole("link", { name: /voir la liste des métiers/i })).toHaveAttribute(
      "href",
      "/metiers",
    );
  });

  it("shows the mes-paris empty state (reusing /mes-paris page copy) when there are no favorites", async () => {
    fetchRecommendationsMock.mockResolvedValue(makeRecoResponse([makeProfession()]));
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voir mes métiers" })).toHaveAttribute(
      "href",
      "/mes-metiers",
    );
  });

  it("AC5 — new profile: métiers and paris empty, progression module still renders first", async () => {
    fetchRecommendationsMock.mockResolvedValue(makeRecoResponse([]));
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings[0]?.textContent).toBe("Ta progression");
    expect(screen.getByTestId("progression-module")).toBeInTheDocument();
    expect(
      screen.getByText(/Tes recommandations arrivent dès que ton profil est prêt/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
  });

  it("degrades the métiers module independently when fetchRecommendations rejects", async () => {
    fetchRecommendationsMock.mockRejectedValue(new Error("ai-service down"));
    fetchMesParisMock.mockResolvedValue([makeSchool({ name: "École A" })]);

    render(await AccueilPage());

    expect(
      screen.getByText(/Tes recommandations arrivent dès que ton profil est prêt/),
    ).toBeInTheDocument();
    // The other module is unaffected.
    expect(screen.getByText("École A")).toBeInTheDocument();
  });

  it("degrades the mes-paris module independently when fetchMesParis rejects", async () => {
    fetchRecommendationsMock.mockResolvedValue(
      makeRecoResponse([makeProfession({ name: "Infirmier" })]),
    );
    fetchMesParisMock.mockRejectedValue(new Error("api down"));

    render(await AccueilPage());

    expect(screen.getByText("Infirmier")).toBeInTheDocument();
    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
  });

  it("code-review fix: a malformed 200 payload (non-array results/schools) renders empty states instead of crashing the page", async () => {
    // These resolve successfully (not a rejection) with a shape that doesn't
    // match the expected contract — `Promise.allSettled` alone does NOT
    // protect against this, only the `Array.isArray` guards in page.tsx do.
    fetchRecommendationsMock.mockResolvedValue({ results: null, computed_at: "x" });
    fetchMesParisMock.mockResolvedValue({ not: "an array" });

    render(await AccueilPage());

    expect(
      screen.getByText(/Tes recommandations arrivent dès que ton profil est prêt/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
  });
});
