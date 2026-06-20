import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EditPassionsSheet } from "../edit-passions-sheet";
import { EditLevelSheet } from "../edit-level-sheet";
import { EditBulletinsSheet } from "../edit-bulletins-sheet";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const mockProfile = {
  passions: ["sciences", "cinema"],
  valeurs: ["autonomie"],
  interets: { "1": "robotique", "2": null, "3": null },
  bulletins_status: "partial" as const,
  bulletins_postponed_at: null,
  bulletins_postponed_banner_dismissed_until: null,
  level: "lycee_terminale",
  filiere: "general",
  specialites: ["mathematiques"],
  sous_filiere_techno: null,
  updated_at: "2026-05-01T10:00:00Z",
};

describe("EditPassionsSheet", () => {
  it("renders when open=true", () => {
    render(
      <EditPassionsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />,
      { wrapper }
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows Sauvegarder and Annuler buttons", () => {
    render(
      <EditPassionsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />,
      { wrapper }
    );
    expect(screen.getByRole("button", { name: /sauvegarder/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /annuler/i })).toBeInTheDocument();
  });

  it("calls onClose when Annuler clicked with no changes", () => {
    const onClose = vi.fn();
    render(
      <EditPassionsSheet open profile={mockProfile} onClose={onClose} onSaved={vi.fn()} />,
      { wrapper }
    );
    fireEvent.click(screen.getByRole("button", { name: /annuler/i }));
    expect(onClose).toHaveBeenCalled();
  });
});

describe("EditLevelSheet", () => {
  it("renders when open=true", () => {
    render(
      <EditLevelSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />,
      { wrapper }
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows level info", () => {
    render(
      <EditLevelSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />,
      { wrapper }
    );
    expect(screen.getByText(/terminale/i)).toBeInTheDocument();
  });
});

describe("EditBulletinsSheet", () => {
  it("renders when open=true", () => {
    render(
      <EditBulletinsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />,
      { wrapper }
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows Ajouter un trimestre button", () => {
    render(
      <EditBulletinsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />,
      { wrapper }
    );
    expect(screen.getByRole("button", { name: /ajouter un trimestre/i })).toBeInTheDocument();
  });
});
