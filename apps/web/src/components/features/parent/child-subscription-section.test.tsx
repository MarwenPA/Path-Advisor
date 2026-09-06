/**
 * <ChildSubscriptionSection> tests — Story 6.4.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const fetchStatusMock = vi.fn();
const createCheckoutMock = vi.fn();
const cancelMock = vi.fn();
vi.mock("@/lib/api/parent", () => ({
  fetchChildSubscriptionStatus: (...args: unknown[]) => fetchStatusMock(...args),
  createChildCheckoutSession: (...args: unknown[]) => createCheckoutMock(...args),
  cancelChildSubscription: (...args: unknown[]) => cancelMock(...args),
}));

import { ChildSubscriptionSection } from "./child-subscription-section";

beforeEach(() => {
  fetchStatusMock.mockReset();
  createCheckoutMock.mockReset();
  cancelMock.mockReset();
  // @ts-expect-error -- jsdom location isn't normally reassignable
  delete window.location;
  // @ts-expect-error -- stub for asserting redirect target
  window.location = { href: "" };
});

describe("ChildSubscriptionSection", () => {
  it("shows the upgrade CTA for a free child", async () => {
    fetchStatusMock.mockResolvedValue({
      tier: "free",
      status: "active",
      current_period_end: null,
      cancel_at_period_end: false,
      is_premium: false,
      paid_by_parent: false,
    });

    render(<ChildSubscriptionSection studentId="stu_1" />);

    expect(
      await screen.findByRole("button", { name: /passer mon enfant en premium/i }),
    ).toBeInTheDocument();
  });

  it("redirects to the checkout URL on upgrade", async () => {
    fetchStatusMock.mockResolvedValue({
      tier: "free",
      status: "active",
      current_period_end: null,
      cancel_at_period_end: false,
      is_premium: false,
      paid_by_parent: false,
    });
    createCheckoutMock.mockResolvedValue({ checkout_url: "https://stripe.test/cs_1" });

    render(<ChildSubscriptionSection studentId="stu_1" />);
    fireEvent.click(await screen.findByRole("button", { name: /passer mon enfant en premium/i }));

    await waitFor(() => expect(window.location.href).toBe("https://stripe.test/cs_1"));
  });

  it("shows premium status + cancel button, marking parent-paid", async () => {
    fetchStatusMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-01T00:00:00Z",
      cancel_at_period_end: false,
      is_premium: true,
      paid_by_parent: true,
    });

    render(<ChildSubscriptionSection studentId="stu_1" />);

    expect(await screen.findByText(/payé par toi/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /annuler l'abonnement/i })).toBeInTheDocument();
  });

  it("cancels and reflects cancel_at_period_end without losing premium", async () => {
    fetchStatusMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-01T00:00:00Z",
      cancel_at_period_end: false,
      is_premium: true,
      paid_by_parent: true,
    });
    cancelMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-01T00:00:00Z",
      cancel_at_period_end: true,
      is_premium: true,
      paid_by_parent: true,
    });

    render(<ChildSubscriptionSection studentId="stu_1" />);
    fireEvent.click(await screen.findByRole("button", { name: /annuler l'abonnement/i }));

    expect(await screen.findByText(/annulation programmée/i)).toBeInTheDocument();
  });
});
