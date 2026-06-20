/**
 * Tests for ReportErrorButton — Story 3.8 AC9 frontend.
 *
 * Strategy: mock ReportErrorForm to avoid Radix Select jsdom interaction issues,
 * test ReportErrorButton state machine independently.
 */

import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ReportErrorButton } from "../ReportErrorButton";

// ─── Mock the hook ────────────────────────────────────────────────────────────

const mockMutate = vi.fn();

vi.mock("@/hooks/useReportProfessionError", () => ({
  useReportProfessionError: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

// ─── Mock ReportErrorForm to avoid Radix Select jsdom crashes ─────────────────

vi.mock("../ReportErrorForm", () => ({
  ReportErrorForm: ({
    onSubmit,
    onCancel,
    submitError,
    isSubmitting,
  }: {
    onSubmit: (p: { error_type: string }) => void;
    onCancel: () => void;
    submitError: string | null;
    isSubmitting: boolean;
    professionName: string;
  }) => (
    <div data-testid="report-form">
      {submitError && <p role="alert">{submitError}</p>}
      <button
        type="button"
        data-testid="submit-btn"
        disabled={isSubmitting}
        onClick={() => onSubmit({ error_type: "description_inexacte" })}
      >
        Envoyer le signalement
      </button>
      <button type="button" onClick={onCancel}>
        Annuler
      </button>
    </div>
  ),
}));

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderButton() {
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <ReportErrorButton professionSlug="infirmier-test" professionName="Infirmier·ère" />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  // Desktop: matchMedia returns matches=false for "(max-width: 1023px)"
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("ReportErrorButton", () => {
  it("renders 'Signaler une erreur' button", () => {
    renderButton();
    expect(screen.getByRole("button", { name: /signaler une erreur/i })).toBeInTheDocument();
  });

  it("opens dialog when button is clicked", async () => {
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /signaler une erreur/i }));
    await waitFor(() => {
      expect(screen.getByTestId("report-form")).toBeInTheDocument();
    });
  });

  it("calls mutate on form submit", async () => {
    mockMutate.mockImplementation(() => {});
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /signaler une erreur/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));
    expect(mockMutate).toHaveBeenCalledWith(
      { error_type: "description_inexacte" },
      expect.any(Object),
    );
  });

  it("shows toast and sets reported state on success", async () => {
    mockMutate.mockImplementation((_p: unknown, { onSuccess }: { onSuccess: () => void }) => {
      onSuccess();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /signaler une erreur/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/merci/i);
    });
    // Button is now in reported state
    const btn = screen.getByRole("button", { name: /erreur déjà signalée/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveTextContent("Signalé");
  });

  it("shows inline error on failure and form stays open", async () => {
    mockMutate.mockImplementation((_p: unknown, { onError }: { onError: () => void }) => {
      onError();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /signaler une erreur/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/envoi échoué/i);
    });
    // Form still visible
    expect(screen.getByTestId("report-form")).toBeInTheDocument();
  });

  it("closes form when Annuler is clicked", async () => {
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /signaler une erreur/i }));
    await waitFor(() => screen.getByRole("button", { name: /annuler/i }));
    fireEvent.click(screen.getByRole("button", { name: /annuler/i }));
    await waitFor(() => {
      expect(screen.queryByTestId("report-form")).not.toBeInTheDocument();
    });
  });

  it("reported button is not clickable after success", async () => {
    mockMutate.mockImplementation((_p: unknown, { onSuccess }: { onSuccess: () => void }) => {
      onSuccess();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /signaler une erreur/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));

    await waitFor(() => screen.getByRole("button", { name: /erreur déjà signalée/i }));
    const reported = screen.getByRole("button", { name: /erreur déjà signalée/i });
    expect(reported).toBeDisabled();
  });
});
