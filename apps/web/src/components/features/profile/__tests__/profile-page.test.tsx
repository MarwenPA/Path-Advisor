import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ProfilePage } from "../profile-page";

vi.mock("@/hooks/use-student-profile", () => ({
  useStudentProfile: () => ({
    data: {
      passions: ["sciences", "cinema"],
      valeurs: ["autonomie"],
      interets: { "1": "robotique", "2": null, "3": null },
      onboarding_step1_status: "completed",
      bulletins_status: "partial",
      bulletins_postponed_at: null,
      bulletins_postponed_banner_dismissed_until: null,
      level: "lycee_terminale",
      filiere: "general",
      specialites: ["mathematiques", "svt"],
      sous_filiere_techno: null,
      updated_at: "2026-05-01T10:00:00Z",
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock("@/components/features/profile/profile-maturity-indicator", () => ({
  ProfileMaturityIndicator: () => <div data-testid="maturity-indicator" />,
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ProfilePage", () => {
  it("renders Mon profil heading", () => {
    render(<ProfilePage />, { wrapper });
    expect(screen.getByRole("heading", { name: /mon profil/i })).toBeInTheDocument();
  });

  it("renders 3 editable sections", () => {
    render(<ProfilePage />, { wrapper });
    expect(screen.getByRole("heading", { name: /passions/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /niveau scolaire/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /bulletins/i })).toBeInTheDocument();
  });

  it("renders maturity indicator", () => {
    render(<ProfilePage />, { wrapper });
    expect(screen.getByTestId("maturity-indicator")).toBeInTheDocument();
  });

  it("shows Modifier button for each section", () => {
    render(<ProfilePage />, { wrapper });
    const modifierBtns = screen.getAllByRole("button", { name: /modifier/i });
    expect(modifierBtns.length).toBeGreaterThanOrEqual(3);
  });

  it("shows current passions summary", () => {
    render(<ProfilePage />, { wrapper });
    expect(screen.getByText(/2 passions/i)).toBeInTheDocument();
  });

  it("shows history link", () => {
    render(<ProfilePage />, { wrapper });
    expect(screen.getByRole("link", { name: /historique/i })).toBeInTheDocument();
  });
});
