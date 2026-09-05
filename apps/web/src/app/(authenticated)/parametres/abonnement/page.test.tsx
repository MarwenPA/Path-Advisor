/**
 * `/parametres/abonnement` page tests — Story 5.3 §T8/AC3.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const getSubscriptionMock = vi.fn();
vi.mock("@/lib/api/billing", () => ({
  getSubscription: () => getSubscriptionMock(),
}));

vi.mock("@/components/features/billing/cancel-subscription-button", () => ({
  CancelSubscriptionButton: () => <button type="button">Annuler mockée</button>,
}));

import AbonnementPage from "./page";

describe("AbonnementPage", () => {
  it("shows the upgrade CTA for a free user", async () => {
    getSubscriptionMock.mockResolvedValue({
      tier: "free",
      status: "active",
      current_period_end: null,
      cancel_at_period_end: false,
      is_premium: false,
    });

    render(await AbonnementPage());

    expect(screen.getByText("Freemium")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /passer en premium/i })).toHaveAttribute(
      "href",
      "/premium",
    );
    expect(screen.queryByRole("button", { name: /annuler mockée/i })).not.toBeInTheDocument();
  });

  it("shows the renewal date + cancel button for an active premium user", async () => {
    getSubscriptionMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-15T00:00:00Z",
      cancel_at_period_end: false,
      is_premium: true,
    });

    render(await AbonnementPage());

    expect(screen.getByText("Premium")).toBeInTheDocument();
    expect(screen.getByText("Actif")).toBeInTheDocument();
    expect(screen.getByText(/renouvellement le 15 octobre 2026/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /annuler mockée/i })).toBeInTheDocument();
  });

  it("shows the scheduled-end message (no cancel button) when cancellation is already scheduled", async () => {
    getSubscriptionMock.mockResolvedValue({
      tier: "premium",
      status: "active",
      current_period_end: "2026-10-15T00:00:00Z",
      cancel_at_period_end: true,
      is_premium: true,
    });

    render(await AbonnementPage());

    expect(screen.getByText(/se termine le 15 octobre 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/déjà programmé pour se terminer/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /annuler mockée/i })).not.toBeInTheDocument();
  });

  it("shows the past_due status label", async () => {
    getSubscriptionMock.mockResolvedValue({
      tier: "premium",
      status: "past_due",
      current_period_end: "2026-10-15T00:00:00Z",
      cancel_at_period_end: false,
      is_premium: true,
    });

    render(await AbonnementPage());

    expect(screen.getByText("Paiement en retard")).toBeInTheDocument();
  });
});
