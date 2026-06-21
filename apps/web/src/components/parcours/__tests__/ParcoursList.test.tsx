import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ParcoursList } from "../ParcoursList";
import type { Parcours } from "@/lib/api/parcours";

// ─── Fixtures ─────────────────────────────────────────────────────────────────

function makeParcours(overrides: Partial<Parcours> = {}): Parcours {
  return {
    id: "test-id-1",
    profession: "prof-1",
    target_school_slug: "lycee-pro-test",
    target_school_name: "Lycée Pro Test",
    niveau_scolaire: "terminale_generale",
    is_default: true,
    nodes: [
      { id: "start", label: "Terminale", type: "start" },
      { id: "target", label: "Lycée Pro Test", type: "target" },
    ],
    edges: [{ source: "start", target: "target" }],
    label: "Parcours principal",
    target_school_affelnet_dates: null,
    target_school_parcoursup_dates: { open: "2026-01-15", close: "2026-03-10" },
    ...overrides,
  };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("ParcoursList", () => {
  // AC5 — niveau badge display

  it('renders "Bac Pro" badge for troisieme_bac_pro', () => {
    const parcours = makeParcours({
      id: "bac-pro-id",
      niveau_scolaire: "troisieme_bac_pro",
      label: "Voie bac pro",
    });
    render(<ParcoursList parcours={[parcours]} />);
    const badge = screen.getByTestId("niveau-badge-bac-pro-id");
    expect(badge.textContent).toBe("Bac Pro");
  });

  it('renders "Terminale" badge for terminale_generale', () => {
    const parcours = makeParcours({
      id: "terminale-id",
      niveau_scolaire: "terminale_generale",
      label: "Voie terminale",
    });
    render(<ParcoursList parcours={[parcours]} />);
    const badge = screen.getByTestId("niveau-badge-terminale-id");
    expect(badge.textContent).toBe("Terminale");
  });

  it('renders "Terminale Techno" badge for terminale_technologique', () => {
    const parcours = makeParcours({
      id: "techno-id",
      niveau_scolaire: "terminale_technologique",
    });
    render(<ParcoursList parcours={[parcours]} />);
    const badge = screen.getByTestId("niveau-badge-techno-id");
    expect(badge.textContent).toBe("Terminale Techno");
  });

  it("no badge rendered when niveau_scolaire is empty string", () => {
    const parcours = makeParcours({
      id: "empty-niveau-id",
      niveau_scolaire: "",
    });
    render(<ParcoursList parcours={[parcours]} />);
    expect(screen.queryByTestId("niveau-badge-empty-niveau-id")).toBeNull();
  });

  it("falls back to the raw niveau value if not in NIVEAU_BADGE map", () => {
    const parcours = makeParcours({
      id: "unknown-niveau-id",
      niveau_scolaire: "seconde",
    });
    render(<ParcoursList parcours={[parcours]} />);
    const badge = screen.getByTestId("niveau-badge-unknown-niveau-id");
    expect(badge.textContent).toBe("seconde");
  });

  // Empty list
  it("renders empty state when no parcours", () => {
    render(<ParcoursList parcours={[]} />);
    expect(screen.getByTestId("parcours-empty")).toBeDefined();
  });

  // Default parcours rendered
  it("renders the default parcours card", () => {
    const parcours = makeParcours({ id: "default-id" });
    render(<ParcoursList parcours={[parcours]} />);
    expect(screen.getByTestId("parcours-card-default-id")).toBeDefined();
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
    render(<ParcoursList parcours={[parcours1, parcours2]} />);
    expect(screen.queryByTestId("alternatives-list")).toBeNull();
    const btn = screen.getByTestId("toggle-alternatives-btn");
    expect(btn.textContent).toContain("Voir d'autres chemins (1)");
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
    render(<ParcoursList parcours={[parcours1, parcours2]} />);
    fireEvent.click(screen.getByTestId("toggle-alternatives-btn"));
    expect(screen.getByTestId("alternatives-list")).toBeDefined();
    expect(screen.getByTestId("parcours-card-p2")).toBeDefined();
  });

  // Alt badge visible without expanding
  it("alt badge is visible in alternatives list", () => {
    const parcours1 = makeParcours({ id: "p1", is_default: true });
    const parcours2 = makeParcours({
      id: "p2",
      is_default: false,
      niveau_scolaire: "troisieme_bac_pro",
    });
    render(<ParcoursList parcours={[parcours1, parcours2]} />);
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
    render(<ParcoursList parcours={[parcours]} />);
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
    render(<ParcoursList parcours={[parcours]} />);
    const datesEl = screen.getByTestId("admission-dates");
    expect(datesEl.textContent).toContain("Affelnet");
    expect(datesEl.textContent).toContain("2026-01-20");
  });

  // Profession name heading
  it("renders profession name heading when provided", () => {
    const parcours = makeParcours({ id: "p1" });
    render(<ParcoursList parcours={[parcours]} professionName="Technicien aéronautique" />);
    expect(screen.getByText(/Parcours pour Technicien aéronautique/)).toBeDefined();
  });
});
