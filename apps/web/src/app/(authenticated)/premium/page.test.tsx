/**
 * `/premium` page tests — Story 5.3 §T6/AC1.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const getSubscriptionMock = vi.fn();
vi.mock("@/lib/api/billing", () => ({
  getSubscription: () => getSubscriptionMock(),
}));

vi.mock("@/components/features/billing/premium-checkout-button", () => ({
  PremiumCheckoutButton: () => <button type="button">CTA mockée</button>,
}));

import PremiumPage from "./page";

describe("PremiumPage", () => {
  it("shows the offer + checkout CTA for a free user", async () => {
    getSubscriptionMock.mockResolvedValue({
      tier: "free",
      status: "active",
      current_period_end: null,
      cancel_at_period_end: false,
      is_premium: false,
    });

    render(await PremiumPage());

    expect(screen.getByRole("heading", { name: /passer en premium/i })).toBeInTheDocument();
    expect(screen.getByText("10,99 € / mois")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cta mockée/i })).toBeInTheDocument();
  });

  it("shows an already-premium message + manage link instead of the CTA for a premium user", async () => {
    getSubscriptionMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-01T00:00:00Z",
      cancel_at_period_end: false,
      is_premium: true,
    });

    render(await PremiumPage());

    expect(screen.getByText(/tu es déjà abonné premium/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /gérer mon abonnement/i })).toHaveAttribute(
      "href",
      "/parametres/abonnement",
    );
    expect(screen.queryByRole("button", { name: /cta mockée/i })).not.toBeInTheDocument();
  });
});
