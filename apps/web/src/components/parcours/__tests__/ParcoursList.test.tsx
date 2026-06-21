import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ParcoursList } from "../ParcoursList";
import type { Parcours } from "../types";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const makeNodes = (count = 2) =>
  Array.from({ length: count }, (_, i) => ({
    id: `node-${i}`,
    label: `Étape ${i + 1}`,
    type: i === 0 ? "start" : i === count - 1 ? "target" : "intermediate",
  }));

const makeParcours = (overrides: Partial<Parcours> = {}): Parcours => ({
  id: crypto.randomUUID(),
  profession: "infirmier-ssr",
  target_school: "school-uuid-1",
  target_school_name: "IFSI Paris",
  target_school_slug: "ifsi-paris",
  target_school_city: "Paris",
  nodes: makeNodes(3),
  edges: [
    { source: "node-0", target: "node-1", weight: 1 },
    { source: "node-1", target: "node-2", weight: 2 },
  ],
  niveau_scolaire: "lycee_1ere_tle_general",
  is_default: true,
  ...overrides,
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("ParcoursList", () => {
  it("renders empty state when parcours array is empty", () => {
    render(<ParcoursList parcours={[]} metiersSlug="infirmier-ssr" />);
    expect(
      screen.getByText(/Aucun parcours disponible pour ce métier pour l'instant\./i),
    ).toBeInTheDocument();
  });

  it("renders the default parcours with school name", () => {
    const p = makeParcours();
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);
    expect(screen.getByText("IFSI Paris")).toBeInTheDocument();
  });

  it("renders a list of nodes from the default parcours", () => {
    const p = makeParcours();
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);
    expect(screen.getByText("Étape 1")).toBeInTheDocument();
    expect(screen.getByText("Étape 2")).toBeInTheDocument();
    expect(screen.getByText("Étape 3")).toBeInTheDocument();
  });

  it("shows 'Voir d'autres chemins (N)' button when there are alternative parcours", () => {
    const p1 = makeParcours({ is_default: true });
    const p2 = makeParcours({
      id: crypto.randomUUID(),
      is_default: false,
      target_school_name: "Autre École",
    });
    const p3 = makeParcours({
      id: crypto.randomUUID(),
      is_default: false,
      target_school_name: "Troisième École",
    });
    render(<ParcoursList parcours={[p1, p2, p3]} metiersSlug="infirmier-ssr" />);
    expect(screen.getByText(/Voir d'autres chemins \(2\)/i)).toBeInTheDocument();
  });

  it("does not show alternatives button when there is only one parcours", () => {
    const p = makeParcours();
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);
    expect(screen.queryByText(/Voir d'autres chemins/i)).not.toBeInTheDocument();
  });

  it("reveals alternative parcours when button is clicked", () => {
    const p1 = makeParcours({ is_default: true });
    const p2 = makeParcours({
      id: crypto.randomUUID(),
      is_default: false,
      target_school_name: "École Alternative",
    });
    render(<ParcoursList parcours={[p1, p2]} metiersSlug="infirmier-ssr" />);

    // Alternative not visible yet
    expect(screen.queryByText("École Alternative")).not.toBeInTheDocument();

    // Click button to expand
    const btn = screen.getByText(/Voir d'autres chemins \(1\)/i);
    fireEvent.click(btn);

    // Now it should be visible
    expect(screen.getByText("École Alternative")).toBeInTheDocument();
  });

  it("renders school grid cards with href=/schools/{slug} for nodes with schoolSlug", () => {
    const nodes = [
      { id: "start", label: "Terminale", type: "start" },
      { id: "school-node", label: "IFSI Paris", type: "intermediate", schoolSlug: "ifsi-paris" },
      { id: "target", label: "Diplômé·e", type: "target", schoolSlug: "universite-paris" },
    ];
    const p = makeParcours({ nodes });
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);

    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));
    expect(hrefs).toContain("/schools/ifsi-paris");
    expect(hrefs).toContain("/schools/universite-paris");
  });
});
