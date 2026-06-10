import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import type { OnboardingStep1Snapshot } from "@/lib/api/onboarding";

const replaceMock = vi.fn();
const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
}));

type HookReturn = {
  snapshot: OnboardingStep1Snapshot;
  isLoading: boolean;
  isFetching: boolean;
  error: unknown;
  submit: ReturnType<typeof vi.fn>;
  isSubmitting: boolean;
  submitError: unknown;
  submitErrorKind: "none" | "client" | "network";
  reset: () => void;
};

let hookReturn: HookReturn;

function makeHook(overrides: Partial<HookReturn> = {}): HookReturn {
  return {
    snapshot: {
      passions: [],
      valeurs: [],
      interets: { "1": null, "2": null, "3": null },
      onboarding_step1_status: "pending",
      onboarding_step1_completed_at: null,
    },
    isLoading: false,
    isFetching: false,
    error: null,
    submit: vi.fn().mockResolvedValue({
      passions: [],
      valeurs: [],
      interets: { "1": null, "2": null, "3": null },
      onboarding_step1_status: "in_progress",
      onboarding_step1_completed_at: null,
    }),
    isSubmitting: false,
    submitError: null,
    submitErrorKind: "none",
    reset: vi.fn(),
    ...overrides,
  };
}

vi.mock("@/hooks/use-onboarding-step-1", () => ({
  useOnboardingStep1: () => hookReturn,
}));

import { OnboardingStep1 } from "./onboarding-step-1";

describe("OnboardingStep1 orchestrator", () => {
  beforeEach(() => {
    replaceMock.mockReset();
    pushMock.mockReset();
    hookReturn = makeHook();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders sub-step 1A on a pending snapshot", () => {
    render(<OnboardingStep1 />);
    expect(screen.getByRole("heading", { name: /qu'est-ce qui te plaît/i })).toBeInTheDocument();
    expect(screen.getByTestId("onboarding-continue")).toBeDisabled();
  });

  it("shows skeleton while loading", () => {
    hookReturn = makeHook({ isLoading: true });
    const { container } = render(<OnboardingStep1 />);
    // Skeleton uses aria-hidden + animate-pulse — assert at least one placeholder block.
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("redirects to /onboarding/step-2 if status is already completed (AC10)", () => {
    hookReturn = makeHook({
      snapshot: {
        passions: ["musique", "sport-corps", "tech-code"],
        valeurs: ["justice-sociale", "creativite", "sens-utilite"],
        interets: { "1": "Sapiens", "2": null, "3": null },
        onboarding_step1_status: "completed",
        onboarding_step1_completed_at: "2026-06-11T00:00:00Z",
      },
    });
    render(<OnboardingStep1 />);
    expect(replaceMock).toHaveBeenCalledWith("/onboarding/step-2");
  });

  it("enables Continue once min 3 passions are selected, then advances to 1B on click", async () => {
    render(<OnboardingStep1 />);
    fireEvent.click(screen.getByRole("checkbox", { name: /musique/i }));
    fireEvent.click(screen.getByRole("checkbox", { name: /tech & code/i }));
    fireEvent.click(screen.getByRole("checkbox", { name: /sport & corps/i }));
    const cta = screen.getByTestId("onboarding-continue");
    expect(cta).not.toBeDisabled();
    fireEvent.click(cta);
    await waitFor(() =>
      expect(hookReturn.submit).toHaveBeenCalledWith({
        step: "passions",
        passions: ["musique", "tech-code", "sport-corps"],
      }),
    );
    // The orchestrator advances to sub-step 2 — heading should be valeurs.
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: /ce qui compte le plus pour toi/i }),
      ).toBeInTheDocument(),
    );
  });

  it("opens skip dialog from header, confirming routes to step-2", async () => {
    render(<OnboardingStep1 />);
    fireEvent.click(screen.getByTestId("onboarding-skip-trigger"));
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /oui, plus tard/i }));
    // ConsentDialog computes a SHA-256 hash via crypto.subtle before calling
    // onAccept — that's async, hence the waitFor.
    await waitFor(() => expect(hookReturn.submit).toHaveBeenCalledWith({ step: "skip" }));
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/onboarding/step-2"));
  });

  it("shows the AC5 'pas de réseau' helper when a NETWORK submit fails (Pass 1 M6)", () => {
    hookReturn = makeHook({
      submitError: new Error("network"),
      isSubmitting: false,
      submitErrorKind: "network",
    });
    render(<OnboardingStep1 />);
    expect(screen.getByTestId("onboarding-helper")).toHaveTextContent(
      /pas de réseau \? pas grave, on enregistre quand tu reviens\./i,
    );
  });

  it("shows a distinct typed helper when a 4xx CLIENT submit fails (Pass 1 M6)", () => {
    // Pass 1 review M6 — a 4xx (CSRF, validation, RBAC) must not surface as a
    // "no network" message: the data won't land on a refresh either. The
    // orchestrator also blocks substep advance for client errors (covered
    // elsewhere); this test asserts the user-visible distinction.
    hookReturn = makeHook({
      submitError: new Error("csrf"),
      isSubmitting: false,
      submitErrorKind: "client",
    });
    render(<OnboardingStep1 />);
    expect(screen.getByTestId("onboarding-helper")).toHaveTextContent(
      /impossible d'enregistrer\. recharge la page et réessaye\./i,
    );
  });

  it("Terminer button is always enabled on sub-step 3 and routes to step-2 after PATCH", async () => {
    hookReturn = makeHook({
      snapshot: {
        passions: ["musique", "tech-code", "sport-corps"],
        valeurs: ["justice-sociale", "creativite", "sens-utilite"],
        interets: { "1": null, "2": null, "3": null },
        onboarding_step1_status: "in_progress",
        onboarding_step1_completed_at: null,
      },
    });
    render(<OnboardingStep1 />);
    // Orchestrator resumes at sub-step 3 since passions + valeurs both have data.
    expect(screen.getByRole("heading", { name: /ce que tu suis, écoutes/i })).toBeInTheDocument();
    const cta = screen.getByTestId("onboarding-continue");
    expect(cta).toHaveTextContent(/terminer/i);
    expect(cta).not.toBeDisabled();
    fireEvent.click(cta);
    await Promise.resolve();
    await Promise.resolve();
    expect(hookReturn.submit).toHaveBeenCalledWith({
      step: "interets",
      interets: { "1": null, "2": null, "3": null },
    });
    expect(pushMock).toHaveBeenCalledWith("/onboarding/step-2");
  });
});
