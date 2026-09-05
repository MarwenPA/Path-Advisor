import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { EditPassionsSheet } from "../edit-passions-sheet";
import { EditLevelSheet } from "../edit-level-sheet";
import { EditBulletinsSheet } from "../edit-bulletins-sheet";

const routerMock = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const patchStep1Mock = vi.fn();
const patchStep2Mock = vi.fn();
const fetchStep2SnapshotMock = vi.fn();
vi.mock("@/lib/api/onboarding", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/api/onboarding")>("@/lib/api/onboarding");
  return {
    ...actual,
    patchOnboardingStep1: (...args: unknown[]) => patchStep1Mock(...args),
    patchOnboardingStep2: (...args: unknown[]) => patchStep2Mock(...args),
    fetchOnboardingStep2Snapshot: (...args: unknown[]) => fetchStep2SnapshotMock(...args),
  };
});

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

const mockStep2Snapshot = {
  level: "lycee_terminale",
  filiere: "general",
  sous_filiere_techno: null,
  specialites: ["mathematiques"],
  intended_track: null,
  postbac_year: null,
  postbac_formation_type: null,
  onboarding_step2_status: "completed" as const,
  onboarding_step2_completed_at: "2026-05-01T10:00:00Z",
  level_ref_version: "2026-05-v1",
};

beforeEach(() => {
  routerMock.push.mockClear();
  patchStep1Mock.mockReset();
  patchStep2Mock.mockReset();
  fetchStep2SnapshotMock.mockReset();
  fetchStep2SnapshotMock.mockResolvedValue(mockStep2Snapshot);
});

describe("EditPassionsSheet", () => {
  it("renders when open=true", () => {
    render(<EditPassionsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows Sauvegarder and Annuler buttons", () => {
    render(<EditPassionsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    expect(screen.getByRole("button", { name: /sauvegarder/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /annuler/i })).toBeInTheDocument();
  });

  it("calls onClose when Annuler clicked with no changes", () => {
    const onClose = vi.fn();
    render(<EditPassionsSheet open profile={mockProfile} onClose={onClose} onSaved={vi.fn()} />, {
      wrapper,
    });
    fireEvent.click(screen.getByRole("button", { name: /annuler/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("renders the real onboarding pickers, pre-filled from the profile", () => {
    render(<EditPassionsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    // PassionsPicker/ValeursPicker render the profile's existing selections
    // as pressed toggles — presence of the section headings is the stable
    // contract to assert on regardless of picker internals.
    expect(screen.getByText("Passions")).toBeInTheDocument();
    expect(screen.getByText("Valeurs")).toBeInTheDocument();
    expect(screen.getByText("Centres d'intérêt")).toBeInTheDocument();
  });

  it("Sauvegarder PATCHes all 3 sub-steps then calls onSaved", async () => {
    patchStep1Mock.mockResolvedValue({});
    const onSaved = vi.fn();
    render(<EditPassionsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={onSaved} />, {
      wrapper,
    });
    fireEvent.click(screen.getByRole("button", { name: /sauvegarder/i }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(patchStep1Mock).toHaveBeenCalledTimes(3);
    const steps = patchStep1Mock.mock.calls.map((call) => call[0].step);
    expect(steps).toEqual(["passions", "valeurs", "interets"]);
  });
});

describe("EditLevelSheet", () => {
  it("renders when open=true", () => {
    render(<EditLevelSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("fetches its own step-2 snapshot and shows the real level picker", async () => {
    render(<EditLevelSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    await waitFor(() => expect(fetchStep2SnapshotMock).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /sauvegarder/i })).not.toBeDisabled(),
    );
  });

  it("Sauvegarder commits via patchOnboardingStep2 then calls onSaved", async () => {
    patchStep2Mock.mockResolvedValue(mockStep2Snapshot);
    const onSaved = vi.fn();
    render(<EditLevelSheet open profile={mockProfile} onClose={vi.fn()} onSaved={onSaved} />, {
      wrapper,
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /sauvegarder/i })).not.toBeDisabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: /sauvegarder/i }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(patchStep2Mock).toHaveBeenCalledWith(
      expect.objectContaining({ commit: true }),
      expect.any(String),
    );
  });
});

describe("EditBulletinsSheet", () => {
  it("renders when open=true", () => {
    render(<EditBulletinsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows the current bulletins status and a link to the real upload flow", () => {
    render(<EditBulletinsSheet open profile={mockProfile} onClose={vi.fn()} onSaved={vi.fn()} />, {
      wrapper,
    });
    expect(screen.getByText(/en cours de vérification/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /gérer mes bulletins/i })).toBeInTheDocument();
  });

  it("navigates to /onboarding/step-3 and closes on click", () => {
    const onClose = vi.fn();
    render(<EditBulletinsSheet open profile={mockProfile} onClose={onClose} onSaved={vi.fn()} />, {
      wrapper,
    });
    fireEvent.click(screen.getByRole("button", { name: /gérer mes bulletins/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(routerMock.push).toHaveBeenCalledWith("/onboarding/step-3");
  });
});
