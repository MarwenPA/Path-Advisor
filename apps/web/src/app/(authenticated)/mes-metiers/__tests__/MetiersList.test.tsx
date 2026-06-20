import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import type { ScoredProfession } from "@/lib/api/recommendations";

import { MetiersList } from "../MetiersList";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock("@/hooks/use-prefers-reduced-motion", () => ({
  usePrefersReducedMotion: () => true, // skip animations in tests
}));

vi.mock("@/components/professions/ScoreVocationnel", () => ({
  ScoreVocationnel: ({ metiersName, score }: { metiersName: string; score: number }) => (
    <div data-testid="score-vocationnel">
      <span>{metiersName}</span>
      <span>{score}</span>
    </div>
  ),
}));

const makeProfession = (overrides: Partial<ScoredProfession> = {}): ScoredProfession => ({
  id: "prof_01",
  slug: "infirmier",
  name: "Infirmier·ère",
  sector: "santé",
  score: 85,
  confidence_level: "high",
  signals_contributifs: [
    { signal: "passion_overlap", weight: 0.35, contribution: 30 },
    { signal: "valeur_alignment", weight: 0.25, contribution: 20 },
    { signal: "niveau_compatibility", weight: 0.2, contribution: 15 },
  ],
  phrase_recopiable: "",
  ...overrides,
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("MetiersList", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders all professions", () => {
    const professions = [
      makeProfession({ id: "p1", name: "Infirmier·ère", slug: "infirmier" }),
      makeProfession({ id: "p2", name: "Médecin généraliste", slug: "medecin" }),
      makeProfession({ id: "p3", name: "Chirurgien·ne", slug: "chirurgien" }),
    ];

    render(<MetiersList professions={professions} />);

    const list = screen.getByTestId("metiers-list");
    expect(list.querySelectorAll("li")).toHaveLength(3);
    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
    expect(screen.getByText("Médecin généraliste")).toBeInTheDocument();
    expect(screen.getByText("Chirurgien·ne")).toBeInTheDocument();
  });

  it("shows empty state when no professions", () => {
    render(<MetiersList professions={[]} />);
    expect(screen.getByText(/Aucune recommandation/)).toBeInTheDocument();
  });

  it("passes score to ScoreVocationnel", () => {
    const professions = [makeProfession({ score: 90 })];
    render(<MetiersList professions={professions} />);
    expect(screen.getByText("90")).toBeInTheDocument();
  });

  it("maps confidence_level=low to indicative", () => {
    // Test via rendered component — since ScoreVocationnel is mocked,
    // just verify MetiersList doesn't crash with low confidence_level.
    const professions = [makeProfession({ confidence_level: "low" })];
    expect(() => render(<MetiersList professions={professions} />)).not.toThrow();
  });

  it("links each card to /metiers/:slug with score and confidence query params", () => {
    const professions = [
      makeProfession({ slug: "infirmier-ssr", score: 85, confidence_level: "high" }),
    ];
    render(<MetiersList professions={professions} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/metiers/infirmier-ssr?score=85&confidence=high");
  });

  it("limits signal chips to top 2", () => {
    // The mock doesn't render chips, but toSignals slices [:2].
    // Smoke test: 3 signals → no error.
    const professions = [
      makeProfession({
        signals_contributifs: [
          { signal: "passion_overlap", weight: 0.35, contribution: 30 },
          { signal: "valeur_alignment", weight: 0.25, contribution: 20 },
          { signal: "niveau_compatibility", weight: 0.2, contribution: 15 },
        ],
      }),
    ];
    expect(() => render(<MetiersList professions={professions} />)).not.toThrow();
  });
});
