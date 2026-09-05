/**
 * <PremiumCheckoutButton> tests — Story 5.3 §T6/AC1.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const redirectMock = vi.fn();
vi.mock("@/lib/stripe/client", () => ({
  redirectToPremiumCheckout: (...args: unknown[]) => redirectMock(...args),
}));

import { PremiumCheckoutButton } from "./premium-checkout-button";

beforeEach(() => {
  redirectMock.mockReset();
});

describe("PremiumCheckoutButton", () => {
  it("calls redirectToPremiumCheckout on click and shows a loading label meanwhile", async () => {
    let resolveRedirect: () => void = () => {};
    redirectMock.mockReturnValue(
      new Promise<void>((resolve) => {
        resolveRedirect = resolve;
      }),
    );

    render(<PremiumCheckoutButton />);
    fireEvent.click(screen.getByRole("button", { name: /passer en premium/i }));

    expect(redirectMock).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /redirection vers le paiement/i })).toBeDisabled(),
    );

    resolveRedirect();
  });

  it("shows an error message if the redirect fails, and re-enables the button", async () => {
    redirectMock.mockRejectedValue(new Error("network down"));

    render(<PremiumCheckoutButton />);
    fireEvent.click(screen.getByRole("button", { name: /passer en premium/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/impossible/i));
    expect(screen.getByRole("button")).not.toBeDisabled();
  });
});
