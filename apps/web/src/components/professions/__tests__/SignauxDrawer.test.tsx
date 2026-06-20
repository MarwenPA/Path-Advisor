import * as React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { SignauxDrawer } from "../SignauxDrawer";
import type { SignalContributif } from "@/lib/api/recommendations";

// jsdom doesn't implement matchMedia — stub it (server snapshot returns false → Dialog, not Sheet)
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

vi.stubGlobal(
  "ResizeObserver",
  vi.fn(() => ({ observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() })),
);

const SIGNALS: SignalContributif[] = [
  { signal: "passion_soins", weight: 0.3, contribution: 12 },
  { signal: "valeur_entraide", weight: 0.2, contribution: 8 },
  { signal: "specialite_svt", weight: 0.15, contribution: 5 },
];

function renderDrawer(props: Partial<React.ComponentProps<typeof SignauxDrawer>> = {}) {
  return render(
    <SignauxDrawer
      open={true}
      onOpenChange={vi.fn()}
      metiersName="Infirmier·ère SSR"
      signals={SIGNALS}
      {...props}
    />,
  );
}

describe("SignauxDrawer", () => {
  it("renders drawer title with profession name", () => {
    renderDrawer();
    expect(screen.getByText(/Pourquoi ce métier/i)).toBeInTheDocument();
  });

  it("renders positive subtitle copy", () => {
    renderDrawer();
    expect(
      screen.getByText(/Voilà les ingrédients qui ont fait monter Infirmier·ère SSR/i),
    ).toBeInTheDocument();
  });

  it("renders all signals sorted by contribution descending", () => {
    renderDrawer();
    const rows = screen.getAllByRole("listitem");
    // First item is highest contribution (12), last is lowest (5)
    expect(rows[0]).toHaveTextContent(/12/);
    expect(rows[1]).toHaveTextContent(/8/);
    expect(rows[2]).toHaveTextContent(/5/);
  });

  it("formats signal labels from underscore_key to readable", () => {
    renderDrawer();
    expect(screen.getByText(/Soins/i)).toBeInTheDocument();
    expect(screen.getByText(/Entraide/i)).toBeInTheDocument();
    expect(screen.getByText(/Svt/i)).toBeInTheDocument();
  });

  it("shows positive contribution with pts suffix", () => {
    renderDrawer();
    expect(screen.getByText(/\+12\s*pts/i)).toBeInTheDocument();
    expect(screen.getByText(/\+8\s*pts/i)).toBeInTheDocument();
  });

  it("renders fallback when signals is empty", () => {
    renderDrawer({ signals: [] });
    expect(screen.getByText(/Les signaux détaillés ne sont pas disponibles/i)).toBeInTheDocument();
  });

  it("renders 'Demander une revue humaine' link", () => {
    renderDrawer();
    expect(screen.getByRole("link", { name: /Demander une revue humaine/i })).toBeInTheDocument();
  });

  it("renders 'Comment ça marche' link", () => {
    renderDrawer();
    expect(screen.getByRole("link", { name: /Comment ça marche/i })).toBeInTheDocument();
  });

  it("calls onOpenChange(false) when close button is clicked", () => {
    const onOpenChange = vi.fn();
    render(
      <SignauxDrawer
        open={true}
        onOpenChange={onOpenChange}
        metiersName="Infirmier·ère SSR"
        signals={SIGNALS}
      />,
    );
    const closeBtn = screen.getByRole("button", { name: /Fermer|Close/i });
    fireEvent.click(closeBtn);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("does not render content when closed", () => {
    render(
      <SignauxDrawer
        open={false}
        onOpenChange={vi.fn()}
        metiersName="Infirmier·ère SSR"
        signals={SIGNALS}
      />,
    );
    expect(screen.queryByText(/Voilà les ingrédients/i)).not.toBeInTheDocument();
  });
});
