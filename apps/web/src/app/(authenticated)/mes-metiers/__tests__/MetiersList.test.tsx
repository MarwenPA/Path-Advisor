import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import type { ScoredProfession } from "@/lib/api/recommendations";

import { MetiersList } from "../MetiersList";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock("@/hooks/use-prefers-reduced-motion", () => ({
  usePrefersReducedMotion: () => true, // skip animations in tests
}));

vi.mock("@/components/professions/ScoreVocationnel", () => ({
  ScoreVocationnel: ({
    metiersName,
    score,
    onSignalClick,
  }: {
    metiersName: string;
    score: number;
    onSignalClick?: (id: string) => void;
  }) => (
    <div data-testid="score-vocationnel">
      <span>{metiersName}</span>
      <span>{score}</span>
      <button
        type="button"
        data-testid="signal-chip-btn"
        onClick={(e) => {
          e.stopPropagation();
          onSignalClick?.("passion_soins");
        }}
      >
        Signal chip
      </button>
    </div>
  ),
}));

vi.mock("@/components/professions/SignauxDrawer", () => ({
  SignauxDrawer: ({
    open,
    metiersName,
    confidenceLevel,
  }: {
    open: boolean;
    onOpenChange: (v: boolean) => void;
    metiersName: string;
    signals: unknown[];
    confidenceLevel?: string;
  }) =>
    open ? (
      <div data-testid="signaux-drawer" data-confidence={confidenceLevel}>
        Drawer: {metiersName}
      </div>
    ) : null,
}));

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

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

  it("shows non-culpabilizing empty state when no professions", () => {
    render(<MetiersList professions={[]} />);
    // AC3 Story 3.10: message must be factual and non-culpabilizing
    const el = screen.getByTestId("metiers-empty");
    expect(el).toBeInTheDocument();
    expect(el.textContent).not.toMatch(/Complète ton profil|manque|insuffisant/i);
    expect(el.textContent).toMatch(/apparaîtront ici/i);
  });

  it("passes score to ScoreVocationnel", () => {
    const professions = [makeProfession({ score: 90 })];
    render(<MetiersList professions={professions} />);
    expect(screen.getByText("90")).toBeInTheDocument();
  });

  it("maps confidence_level=low to indicative", () => {
    const professions = [makeProfession({ confidence_level: "low" })];
    expect(() => render(<MetiersList professions={professions} />)).not.toThrow();
  });

  it("links each card to /metiers/:slug with score, confidence, and signals query params", () => {
    const profession = makeProfession({
      slug: "infirmier-ssr",
      score: 85,
      confidence_level: "high",
    });
    render(<MetiersList professions={[profession]} />);
    const link = screen.getByRole("link");
    const href = link.getAttribute("href") ?? "";
    expect(href).toMatch(/^\/metiers\/infirmier-ssr\?score=85&confidence=high&signals=/);
  });

  it("limits signal chips to top 2", () => {
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

  it("opens SignauxDrawer when a signal chip is clicked", () => {
    const professions = [makeProfession({ name: "Infirmier·ère SSR" })];
    render(<MetiersList professions={professions} />);

    expect(screen.queryByTestId("signaux-drawer")).not.toBeInTheDocument();

    const chip = screen.getByTestId("signal-chip-btn");
    fireEvent.click(chip);

    expect(screen.getByTestId("signaux-drawer")).toBeInTheDocument();
    expect(screen.getByTestId("signaux-drawer")).toHaveTextContent("Infirmier·ère SSR");
  });

  it("does not open drawer when card body is clicked (link navigates normally)", () => {
    const professions = [makeProfession()];
    render(<MetiersList professions={professions} />);
    // Clicking the link itself (not chip) should NOT open the drawer
    expect(screen.queryByTestId("signaux-drawer")).not.toBeInTheDocument();
  });

  // ── Story 3.10: confidenceLevel propagated to SignauxDrawer ────────────────

  it("passes confidence_level=low to SignauxDrawer when chip clicked", () => {
    const professions = [makeProfession({ name: "Kiné", confidence_level: "low" })];
    render(<MetiersList professions={professions} />);
    fireEvent.click(screen.getByTestId("signal-chip-btn"));
    const drawer = screen.getByTestId("signaux-drawer");
    expect(drawer).toHaveAttribute("data-confidence", "low");
  });

  it("passes confidence_level=high to SignauxDrawer when chip clicked", () => {
    const professions = [makeProfession({ name: "Kiné", confidence_level: "high" })];
    render(<MetiersList professions={professions} />);
    fireEvent.click(screen.getByTestId("signal-chip-btn"));
    const drawer = screen.getByTestId("signaux-drawer");
    expect(drawer).toHaveAttribute("data-confidence", "high");
  });

  it("shows niveau-adapted banner when niveauAdapted=true", () => {
    render(<MetiersList professions={[makeProfession()]} niveauAdapted={true} />);
    const banner = screen.getByTestId("niveau-adapted-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toMatch(/niveau scolaire/i);
  });

  it("hides niveau-adapted banner when niveauAdapted=false", () => {
    render(<MetiersList professions={[makeProfession()]} niveauAdapted={false} />);
    expect(screen.queryByTestId("niveau-adapted-banner")).not.toBeInTheDocument();
  });

  it("hides niveau-adapted banner when niveauAdapted is omitted", () => {
    render(<MetiersList professions={[makeProfession()]} />);
    expect(screen.queryByTestId("niveau-adapted-banner")).not.toBeInTheDocument();
  });
});
