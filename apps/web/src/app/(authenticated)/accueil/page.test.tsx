/**
 * `/accueil` page tests — Story 8.8 §T4.1.
 *
 * Server Component: awaited directly then rendered, mirroring the pattern in
 * `app/page.test.tsx` — mocks by module (`@/lib/api/mes-paris`), never a
 * global `fetch` mock. `ProgressionModule` is mocked as a whole (it is a
 * client component with its own data-fetching lifecycle, covered indirectly
 * here and directly by `profile-maturity-indicator.test.tsx`).
 *
 * "Tes métiers" (2026-09-05, explicit request): dropped the score-card
 * examples entirely, always just a link to the full catalog — no more
 * `fetchRecommendations()` call from this page, nothing to mock here.
 */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { School } from "@/lib/api/schools";

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

beforeEach(() => {
  fetchMesParisMock.mockReset();
});

describe("AccueilPage", () => {
  it("renders 3 sections in order: progression, métiers, paris", async () => {
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

  it("Tes métiers always shows a single link to the full catalog, no example cards", async () => {
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    expect(screen.getByRole("link", { name: /voir la liste des métiers/i })).toHaveAttribute(
      "href",
      "/metiers",
    );
    expect(screen.queryByTestId("accueil-metiers-list")).not.toBeInTheDocument();
  });

  it("Tes paris always shows a link to the full schools catalog, regardless of favorites", async () => {
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    expect(screen.getByRole("link", { name: /voir la liste des établissements/i })).toHaveAttribute(
      "href",
      "/schools",
    );
  });

  it("shows the top-3 mes-paris schools with a link to /mes-paris", async () => {
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

  it("shows the mes-paris empty state when there are no favorites", async () => {
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voir mes métiers" })).toHaveAttribute(
      "href",
      "/mes-metiers",
    );
  });

  it("AC5 — new profile: paris empty, progression module still renders first, métiers always shows its link", async () => {
    fetchMesParisMock.mockResolvedValue([]);

    render(await AccueilPage());

    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings[0]?.textContent).toBe("Ta progression");
    expect(screen.getByTestId("progression-module")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /voir la liste des métiers/i })).toBeInTheDocument();
    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
  });

  it("degrades the mes-paris module independently when fetchMesParis rejects", async () => {
    fetchMesParisMock.mockRejectedValue(new Error("api down"));

    render(await AccueilPage());

    expect(screen.getByRole("link", { name: /voir la liste des métiers/i })).toBeInTheDocument();
    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
  });

  it("code-review fix: a malformed 200 payload (non-array schools) renders the mes-paris empty state instead of crashing the page", async () => {
    // This resolves successfully (not a rejection) with a shape that doesn't
    // match the expected contract — `Promise.allSettled` alone does NOT
    // protect against this, only the `Array.isArray` guard in page.tsx does.
    fetchMesParisMock.mockResolvedValue({ not: "an array" });

    render(await AccueilPage());

    expect(screen.getByText(/Tu n'as pas encore exploré tes premiers paris/)).toBeInTheDocument();
  });
});
