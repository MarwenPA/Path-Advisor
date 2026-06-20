/**
 * Tests for ReviewRequestButton — Story 3.7 AC9 frontend.
 *
 * Strategy: mock ReviewRequestForm to avoid Radix Select jsdom crashes,
 * test ReviewRequestButton state machine in isolation.
 */

import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ReviewRequestButton } from "../ReviewRequestButton";

// ─── Mock the hook ────────────────────────────────────────────────────────────

const mockMutate = vi.fn();

vi.mock("@/hooks/useRequestRecommendationReview", () => ({
  useRequestRecommendationReview: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

// ─── Mock ReviewRequestForm to avoid Radix Select jsdom crashes ──────────────

vi.mock("../ReviewRequestForm", () => ({
  ReviewRequestForm: ({
    onSubmit,
    onCancel,
    submitError,
    isSubmitting,
    professionSlug,
  }: {
    onSubmit: (p: { profession_slug: string; reason: string }) => void;
    onCancel: () => void;
    submitError: string | null;
    isSubmitting: boolean;
    professionName: string;
    professionSlug: string;
  }) => (
    <div data-testid="review-form">
      {submitError && <p role="alert">{submitError}</p>}
      <button
        type="button"
        data-testid="submit-btn"
        disabled={isSubmitting}
        onClick={() => onSubmit({ profession_slug: professionSlug, reason: "ne_correspond_pas" })}
      >
        Envoyer la demande
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

function renderButton(props?: Partial<React.ComponentProps<typeof ReviewRequestButton>>) {
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <ReviewRequestButton
        professionSlug="medecin-generaliste"
        professionName="Médecin généraliste"
        hasScore={true}
        {...props}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  // jsdom doesn't implement matchMedia — stub it (server snapshot returns false → Dialog, not Sheet)
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

describe("ReviewRequestButton", () => {
  it("renders the trigger button when hasScore is true", () => {
    renderButton();
    expect(screen.getByRole("button", { name: /demander une revue/i })).toBeInTheDocument();
  });

  it("does not render anything when hasScore is false", () => {
    renderButton({ hasScore: false });
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("opens the form when the trigger button is clicked", () => {
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    expect(screen.getByTestId("review-form")).toBeInTheDocument();
  });

  it("closes the form when Annuler is clicked", () => {
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    fireEvent.click(screen.getByRole("button", { name: /annuler/i }));
    expect(screen.queryByTestId("review-form")).not.toBeInTheDocument();
  });

  it("calls mutate when form is submitted", () => {
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    fireEvent.click(screen.getByTestId("submit-btn"));
    expect(mockMutate).toHaveBeenCalledWith(
      { profession_slug: "medecin-generaliste", reason: "ne_correspond_pas" },
      expect.any(Object),
    );
  });

  it("transitions to reviewRequested state on success", async () => {
    mockMutate.mockImplementation((_payload: unknown, { onSuccess }: { onSuccess: () => void }) => {
      onSuccess();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });
    const btn = screen.getByRole("button", { name: /revue humaine déjà demandée/i });
    expect(btn).toBeDisabled();
  });

  it("shows toast after successful submission", async () => {
    mockMutate.mockImplementation((_payload: unknown, { onSuccess }: { onSuccess: () => void }) => {
      onSuccess();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/7 jours ouvrés/i);
    });
  });

  it("shows inline error and keeps form open on network failure", async () => {
    mockMutate.mockImplementation((_payload: unknown, { onError }: { onError: () => void }) => {
      onError();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    fireEvent.click(screen.getByTestId("submit-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/envoi échoué/i);
    });
    expect(screen.getByTestId("review-form")).toBeInTheDocument();
  });

  it("button is disabled and labelled correctly in reviewRequested state", async () => {
    mockMutate.mockImplementation((_payload: unknown, { onSuccess }: { onSuccess: () => void }) => {
      onSuccess();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });
    const btn = screen.getByRole("button", { name: /revue humaine déjà demandée/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveTextContent("Revue demandée");
  });

  it("does not open form when already in reviewRequested state", async () => {
    mockMutate.mockImplementation((_payload: unknown, { onSuccess }: { onSuccess: () => void }) => {
      onSuccess();
    });
    renderButton();
    fireEvent.click(screen.getByRole("button", { name: /demander une revue/i }));
    await waitFor(() => screen.getByTestId("submit-btn"));
    fireEvent.click(screen.getByTestId("submit-btn"));
    await waitFor(() => screen.getByRole("status"));
    const btn = screen.getByRole("button", { name: /revue humaine déjà demandée/i });
    fireEvent.click(btn);
    expect(screen.queryByTestId("review-form")).not.toBeInTheDocument();
  });
});
