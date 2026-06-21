import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ParcoursList } from "../ParcoursList";
import type { Parcours } from "../types";

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const makeNodes = (count = 2) =>
  Array.from({ length: count }, (_, i) => ({
    id: `node-${i}`,
    label: `Étape ${i + 1}`,
    type: i === 0 ? "start" : i === count - 1 ? "target" : "intermediate",
  }));

function makeParcours(overrides: Partial<Parcours> = {}): Parcours {
  return {
    id: "test-id-1",
    profession: "prof-1",
    target_school: "school-uuid-1",
    target_school_slug: "lycee-pro-test",
    target_school_name: "Lycée Pro Test",
    target_school_city: "Paris",
    niveau_scolaire: "terminale_generale",
    is_default: true,
    nodes: makeNodes(3),
    edges: [
      { source: "node-0", target: "node-1", weight: 1 },
      { source: "node-1", target: "node-2", weight: 2 },
    ],
    label: "Parcours principal",
    target_school_affelnet_dates: null,
    target_school_parcoursup_dates: { open: "2026-01-15", close: "2026-03-10" },
    target_school_tuition_max: null,
    target_school_selectivity: null,
    target_school_apprenticeship: null,
    target_school_internship: null,
    ...overrides,
  };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("ParcoursList", () => {
  // AC5 — niveau badge display (Story 4.7)

  it('renders "Bac Pro" badge for troisieme_bac_pro', () => {
    const parcours = makeParcours({
      id: "bac-pro-id",
      niveau_scolaire: "troisieme_bac_pro",
      label: "Voie bac pro",
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    const badge = screen.getByTestId("niveau-badge-bac-pro-id");
    expect(badge.textContent).toBe("Bac Pro");
  });

  it('renders "Terminale" badge for terminale_generale', () => {
    const parcours = makeParcours({
      id: "terminale-id",
      niveau_scolaire: "terminale_generale",
      label: "Voie terminale",
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    const badge = screen.getByTestId("niveau-badge-terminale-id");
    expect(badge.textContent).toBe("Terminale");
  });

  it('renders "Terminale Techno" badge for terminale_technologique', () => {
    const parcours = makeParcours({
      id: "techno-id",
      niveau_scolaire: "terminale_technologique",
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    const badge = screen.getByTestId("niveau-badge-techno-id");
    expect(badge.textContent).toBe("Terminale Techno");
  });

  it("no badge rendered when niveau_scolaire is empty string", () => {
    const parcours = makeParcours({
      id: "empty-niveau-id",
      niveau_scolaire: "",
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    expect(screen.queryByTestId("niveau-badge-empty-niveau-id")).toBeNull();
  });

  it("falls back to the raw niveau value if not in NIVEAU_BADGE map", () => {
    const parcours = makeParcours({
      id: "unknown-niveau-id",
      niveau_scolaire: "seconde",
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    const badge = screen.getByTestId("niveau-badge-unknown-niveau-id");
    expect(badge.textContent).toBe("seconde");
  });

  // Empty list
  it("renders empty state when no parcours", () => {
    render(<ParcoursList parcours={[]} metiersSlug="prof-1" />);
    expect(screen.getByTestId("parcours-empty")).toBeDefined();
  });

  // Default parcours rendered
  it("renders the default parcours card", () => {
    const parcours = makeParcours({ id: "default-id" });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    expect(screen.getByTestId("parcours-card-default-id")).toBeDefined();
  });

  // Story 4.3 — renders school name
  it("renders the default parcours with school name", () => {
    const p = makeParcours({ target_school_name: "IFSI Paris" });
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);
    expect(screen.getByText("IFSI Paris")).toBeInTheDocument();
  });

  // Story 4.3 — renders nodes
  it("renders a list of nodes from the default parcours", () => {
    const p = makeParcours({ nodes: makeNodes(3) });
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);
    expect(screen.getByText("Étape 1")).toBeInTheDocument();
    expect(screen.getByText("Étape 2")).toBeInTheDocument();
    expect(screen.getByText("Étape 3")).toBeInTheDocument();
  });

  // Alternatives collapsed by default
  it("alternatives are hidden by default", () => {
    const parcours1 = makeParcours({ id: "p1", is_default: true });
    const parcours2 = makeParcours({
      id: "p2",
      is_default: false,
      niveau_scolaire: "troisieme_bac_pro",
      label: "Alternative bac pro",
    });
    render(<ParcoursList parcours={[parcours1, parcours2]} metiersSlug="prof-1" />);
    expect(screen.queryByTestId("alternatives-list")).toBeNull();
    const btn = screen.getByTestId("toggle-alternatives-btn");
    expect(btn.textContent).toContain("Voir d'autres chemins (1)");
  });

  // Shows 'Voir d'autres chemins (N)' button for multiple alternatives
  it("shows 'Voir d'autres chemins (2)' button when there are 2 alternatives", () => {
    const p1 = makeParcours({ id: "p1", is_default: true });
    const p2 = makeParcours({ id: "p2", is_default: false, target_school_name: "Autre École" });
    const p3 = makeParcours({ id: "p3", is_default: false, target_school_name: "Troisième École" });
    render(<ParcoursList parcours={[p1, p2, p3]} metiersSlug="infirmier-ssr" />);
    expect(screen.getByText(/Voir d'autres chemins \(2\)/i)).toBeInTheDocument();
  });

  // No alternatives button with single parcours
  it("does not show alternatives button when there is only one parcours", () => {
    const p = makeParcours();
    render(<ParcoursList parcours={[p]} metiersSlug="infirmier-ssr" />);
    expect(screen.queryByText(/Voir d'autres chemins/i)).not.toBeInTheDocument();
  });

  // Alternatives shown after click
  it("shows alternatives when button clicked", () => {
    const parcours1 = makeParcours({ id: "p1", is_default: true });
    const parcours2 = makeParcours({
      id: "p2",
      is_default: false,
      niveau_scolaire: "troisieme_bac_pro",
      label: "Alternative bac pro",
    });
    render(<ParcoursList parcours={[parcours1, parcours2]} metiersSlug="prof-1" />);
    fireEvent.click(screen.getByTestId("toggle-alternatives-btn"));
    expect(screen.getByTestId("alternatives-list")).toBeDefined();
    expect(screen.getByTestId("parcours-card-p2")).toBeDefined();
  });

  // Reveals alternative parcours by name
  it("reveals alternative parcours when button is clicked", () => {
    const p1 = makeParcours({ id: "p1", is_default: true });
    const p2 = makeParcours({
      id: "p2",
      is_default: false,
      target_school_name: "École Alternative",
    });
    render(<ParcoursList parcours={[p1, p2]} metiersSlug="infirmier-ssr" />);
    expect(screen.queryByText("École Alternative")).not.toBeInTheDocument();
    const btn = screen.getByText(/Voir d'autres chemins \(1\)/i);
    fireEvent.click(btn);
    expect(screen.getByText("École Alternative")).toBeInTheDocument();
  });

  // Alt badge visible in alternatives list
  it("alt badge is visible in alternatives list", () => {
    const parcours1 = makeParcours({ id: "p1", is_default: true });
    const parcours2 = makeParcours({
      id: "p2",
      is_default: false,
      niveau_scolaire: "troisieme_bac_pro",
    });
    render(<ParcoursList parcours={[parcours1, parcours2]} metiersSlug="prof-1" />);
    fireEvent.click(screen.getByTestId("toggle-alternatives-btn"));
    const altBadge = screen.getByTestId("alt-badge-p2");
    expect(altBadge.textContent).toBe("Bac Pro");
  });

  // Admission dates — parcoursup shown for terminale_generale
  it("shows parcoursup dates for terminale_generale", () => {
    const parcours = makeParcours({
      id: "p1",
      niveau_scolaire: "terminale_generale",
      target_school_parcoursup_dates: { open: "2026-01-15", close: "2026-03-10" },
      target_school_affelnet_dates: null,
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    const datesEl = screen.getByTestId("admission-dates");
    expect(datesEl.textContent).toContain("Parcoursup");
    expect(datesEl.textContent).toContain("2026-01-15");
  });

  // Admission dates — affelnet shown for troisieme_bac_pro
  it("shows affelnet dates for troisieme_bac_pro", () => {
    const parcours = makeParcours({
      id: "p1",
      niveau_scolaire: "troisieme_bac_pro",
      target_school_affelnet_dates: { open: "2026-01-20", close: "2026-03-10" },
      target_school_parcoursup_dates: null,
    });
    render(<ParcoursList parcours={[parcours]} metiersSlug="prof-1" />);
    const datesEl = screen.getByTestId("admission-dates");
    expect(datesEl.textContent).toContain("Affelnet");
    expect(datesEl.textContent).toContain("2026-01-20");
  });

  // Profession name heading
  it("renders profession name heading when provided", () => {
    const parcours = makeParcours({ id: "p1" });
    render(
      <ParcoursList
        parcours={[parcours]}
        metiersSlug="prof-1"
        professionName="Technicien aéronautique"
      />,
    );
    expect(screen.getByText(/Parcours pour Technicien aéronautique/)).toBeDefined();
  });

  // Story 4.3 — school grid with hrefs
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
