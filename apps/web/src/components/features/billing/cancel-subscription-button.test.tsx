/**
 * <CancelSubscriptionButton> tests — Story 5.3 §T8/AC3.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const routerMock = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const cancelMock = vi.fn();
vi.mock("@/lib/api/billing", () => ({
  cancelSubscription: (...args: unknown[]) => cancelMock(...args),
}));

import { CancelSubscriptionButton } from "./cancel-subscription-button";

beforeEach(() => {
  routerMock.refresh.mockClear();
  cancelMock.mockReset();
});

describe("CancelSubscriptionButton", () => {
  it("opens a confirmation dialog on click", async () => {
    render(<CancelSubscriptionButton />);
    fireEvent.click(screen.getByRole("button", { name: /annuler mon abonnement/i }));

    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    expect(screen.getByText(/annuler ton abonnement premium/i)).toBeInTheDocument();
  });

  it("calls cancelSubscription then router.refresh on confirm", async () => {
    cancelMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-15T00:00:00Z",
      cancel_at_period_end: true,
      is_premium: true,
    });

    render(<CancelSubscriptionButton />);
    fireEvent.click(screen.getByRole("button", { name: /annuler mon abonnement/i }));
    await screen.findByRole("dialog");
    fireEvent.click(screen.getByRole("button", { name: /confirmer l'annulation/i }));

    await waitFor(() => expect(cancelMock).toHaveBeenCalledTimes(1));
    expect(routerMock.refresh).toHaveBeenCalledTimes(1);
    // Dialog closes on success.
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("shows an error message and keeps the dialog reusable when cancellation fails", async () => {
    cancelMock.mockRejectedValue(new Error("stripe down"));

    render(<CancelSubscriptionButton />);
    fireEvent.click(screen.getByRole("button", { name: /annuler mon abonnement/i }));
    await screen.findByRole("dialog");
    fireEvent.click(screen.getByRole("button", { name: /confirmer l'annulation/i }));

    // findByText polls — handles the async state flip from "submitting" → "error"
    // (same pattern as revoke-access-button.test.tsx's 5xx case).
    const errorEl = await screen.findByText(/échoué/i, {}, { timeout: 3000 });
    expect(errorEl).toBeInTheDocument();
    expect(routerMock.refresh).not.toHaveBeenCalled();
  });
});
