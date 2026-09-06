import * as React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { FicheMetierClient } from "../FicheMetierClient";
import type { Profession } from "@/components/professions/types";
import type { SignalContributif } from "@/lib/api/recommendations";

// ─── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@/components/professions/FicheMetier", () => ({
  FicheMetier: ({
    profession,
    onSignalClick,
  }: {
    profession: Profession;
    onSignalClick?: (id: string) => void;
  }) => (
    <div data-testid="fiche-metier">
      <span>{profession.name}</span>
      <button
        type="button"
        data-testid="signal-click-btn"
        onClick={() => onSignalClick?.("passion_soins")}
      >
        Chip signal
      </button>
    </div>
  ),
}));

vi.mock("@/components/professions/SignauxDrawer", () => ({
  SignauxDrawer: ({
    open,
    metiersName,
    signals,
    confidenceLevel,
  }: {
    open: boolean;
    onOpenChange: (v: boolean) => void;
    metiersName: string;
    signals: SignalContributif[];
    confidenceLevel?: string;
  }) =>
    open ? (
      <div data-testid="signaux-drawer" data-confidence={confidenceLevel}>
        {metiersName} — {signals.length} signaux
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

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const PROFESSION: Profession = {
  id: "prof_01",
  slug: "infirmier-ssr",
  name: "Infirmier·ère SSR",
  description: "Soins de suite.",
  daily_routine: "Tour des chambres.",
  requirements_json: [{ type: "studies", label: "Diplôme infirmier" }],
  prospects_text: "Évolution vers cadre de santé.",
  median_salary_eur: 28000,
  salary_range_json: { min: 24000, max: 38000 },
  signals_json: { passions: ["soins"], valeurs: ["entraide"], specialites: ["svt"] },
  level_compatibility: ["lycee_1ere_tle_general"],
  sector: "santé",
};

const SIGNALS: SignalContributif[] = [
  { signal: "passion_soins", weight: 0.3, contribution: 12 },
  { signal: "valeur_entraide", weight: 0.2, contribution: 8 },
];

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("FicheMetierClient", () => {
  it("renders FicheMetier with profession name", () => {
    render(<FicheMetierClient profession={PROFESSION} signalsContributifs={SIGNALS} />);
    expect(screen.getByTestId("fiche-metier")).toBeInTheDocument();
    expect(screen.getByText("Infirmier·ère SSR")).toBeInTheDocument();
  });

  it("drawer is closed initially", () => {
    render(<FicheMetierClient profession={PROFESSION} signalsContributifs={SIGNALS} />);
    expect(screen.queryByTestId("signaux-drawer")).not.toBeInTheDocument();
  });

  it("opens SignauxDrawer when a signal chip is clicked", () => {
    render(<FicheMetierClient profession={PROFESSION} signalsContributifs={SIGNALS} />);
    fireEvent.click(screen.getByTestId("signal-click-btn"));
    expect(screen.getByTestId("signaux-drawer")).toBeInTheDocument();
    expect(screen.getByTestId("signaux-drawer")).toHaveTextContent("Infirmier·ère SSR");
  });

  it("filters drawer to the clicked signal when found", () => {
    render(<FicheMetierClient profession={PROFESSION} signalsContributifs={SIGNALS} />);
    fireEvent.click(screen.getByTestId("signal-click-btn")); // fires "passion_soins"
    expect(screen.getByTestId("signaux-drawer")).toHaveTextContent("1 signaux");
  });

  it("opens drawer with empty signals when signalsContributifs is empty", () => {
    render(<FicheMetierClient profession={PROFESSION} signalsContributifs={[]} />);
    fireEvent.click(screen.getByTestId("signal-click-btn"));
    expect(screen.getByTestId("signaux-drawer")).toBeInTheDocument();
    expect(screen.getByTestId("signaux-drawer")).toHaveTextContent("0 signaux");
  });

  it("passes score and confidenceLevel to FicheMetier", () => {
    render(
      <FicheMetierClient
        profession={PROFESSION}
        score={85}
        confidenceLevel="normal"
        signalsContributifs={SIGNALS}
      />,
    );
    // FicheMetier is mocked — just verify no crash
    expect(screen.getByTestId("fiche-metier")).toBeInTheDocument();
  });

  // ── Story 3.10: drawerConfidenceLevel propagated to SignauxDrawer ─────────

  it("passes drawerConfidenceLevel=low to SignauxDrawer when chip clicked", () => {
    render(
      <FicheMetierClient
        profession={PROFESSION}
        signalsContributifs={SIGNALS}
        drawerConfidenceLevel="low"
      />,
    );
    fireEvent.click(screen.getByTestId("signal-click-btn"));
    expect(screen.getByTestId("signaux-drawer")).toHaveAttribute("data-confidence", "low");
  });

  it("passes drawerConfidenceLevel=medium to SignauxDrawer when chip clicked", () => {
    render(
      <FicheMetierClient
        profession={PROFESSION}
        signalsContributifs={SIGNALS}
        drawerConfidenceLevel="medium"
      />,
    );
    fireEvent.click(screen.getByTestId("signal-click-btn"));
    expect(screen.getByTestId("signaux-drawer")).toHaveAttribute("data-confidence", "medium");
  });

  it("does not pass confidenceLevel to SignauxDrawer when drawerConfidenceLevel is absent", () => {
    render(<FicheMetierClient profession={PROFESSION} signalsContributifs={SIGNALS} />);
    fireEvent.click(screen.getByTestId("signal-click-btn"));
    expect(screen.getByTestId("signaux-drawer")).not.toHaveAttribute("data-confidence");
  });
});
