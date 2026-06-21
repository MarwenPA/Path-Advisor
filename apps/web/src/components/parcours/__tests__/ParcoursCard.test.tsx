import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ParcoursCard } from "../ParcoursCard";
import type { Parcours } from "../types";

// Mock CarteAdmission
vi.mock("@/components/schools/CarteAdmission", () => ({
  CarteAdmission: ({ schoolName, variant }: { schoolName: string; variant: string }) => (
    <div data-testid="carte-admission" data-variant={variant}>
      {schoolName}
    </div>
  ),
}));

// Mock MiniGraph
vi.mock("../MiniGraph", () => ({
  MiniGraph: () => <svg data-testid="mini-graph" />,
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

const baseParcours: Parcours = {
  id: "p-1",
  profession: "Medecin",
  target_school: "ecole-abc",
  target_school_name: "Ecole ABC",
  target_school_slug: "ecole-abc",
  target_school_city: "Paris",
  nodes: [
    { id: "n1", label: "Lycée", type: "start" },
    { id: "n2", label: "BTS", type: "intermediate" },
    { id: "n3", label: "Ecole ABC", type: "target" },
  ],
  edges: [
    { source: "n1", target: "n2" },
    { source: "n2", target: "n3" },
  ],
  niveau_scolaire: "Bac+2",
  is_default: false,
  label: "Parcours standard",
  updated_at: "2026-06-20T10:00:00Z",
  created_at: "2026-06-01T00:00:00Z",
  target_school_affelnet_dates: null,
  target_school_parcoursup_dates: null,
  target_school_tuition_max: null,
  target_school_selectivity: null,
  target_school_apprenticeship: null,
  target_school_internship: null,
};

const parcoursWithAdmissionStat: Parcours = {
  ...baseParcours,
  nodes: [
    { id: "n1", label: "Lycée", type: "start" },
    { id: "n2", label: "BTS", type: "intermediate" },
    {
      id: "n3",
      label: "Ecole ABC",
      type: "target",
      admission_stat: {
        expected_proba: 65,
        label: "realiste",
        context_line: "Moyenne admise 2024 : 14,5",
        action_lever: null,
      },
    },
  ],
};

describe("ParcoursCard", () => {
  it("renders school name from target_school_name", () => {
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" />);
    expect(screen.getByText("Ecole ABC")).toBeDefined();
  });

  it("renders niveau_scolaire when present", () => {
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" />);
    expect(screen.getByText("Bac+2")).toBeDefined();
  });

  it("does not render CarteAdmission when no admission_stat on target node", () => {
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" />);
    expect(screen.queryByTestId("carte-admission")).toBeNull();
  });

  it("renders CarteAdmission when target node has admission_stat", () => {
    render(<ParcoursCard parcours={parcoursWithAdmissionStat} metiersSlug="medecin" />);
    const carteAdmission = screen.getByTestId("carte-admission");
    expect(carteAdmission).toBeDefined();
    expect(carteAdmission.getAttribute("data-variant")).toBe("small");
  });

  it('renders "Voir la fiche" link pointing to /schools/{school_slug}', () => {
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" />);
    const link = screen.getByText("Voir la fiche");
    // Should use target_school_slug when available
    expect(link.getAttribute("href")).toBe("/schools/ecole-abc");
  });

  it("renders Capturer button when onCapture provided", () => {
    const onCapture = vi.fn();
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" onCapture={onCapture} />);
    expect(screen.getByText("Capturer")).toBeDefined();
  });

  it("does not render Capturer when onCapture absent", () => {
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" />);
    expect(screen.queryByText("Capturer")).toBeNull();
  });

  it("Capturer button calls onCapture with parcours.id", () => {
    const onCapture = vi.fn();
    render(<ParcoursCard parcours={baseParcours} metiersSlug="medecin" onCapture={onCapture} />);
    fireEvent.click(screen.getByText("Capturer"));
    expect(onCapture).toHaveBeenCalledTimes(1);
    expect(onCapture).toHaveBeenCalledWith("p-1");
  });
});
