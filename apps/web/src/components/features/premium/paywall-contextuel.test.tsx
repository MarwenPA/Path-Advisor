/**
 * <PaywallContextuel> tests — Story 5.11.
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, beforeEach } from "vitest";

import { PaywallContextuel } from "./paywall-contextuel";

const PROPS = {
  feature: "test-feature",
  title: "Cette feature est en premium",
  description: "Description factuelle.",
  benefits: ["Bénéfice un", "Bénéfice deux"],
};

beforeEach(() => {
  sessionStorage.clear();
});

describe("PaywallContextuel", () => {
  it("opens the sheet on trigger click, showing title/description/benefits", () => {
    render(
      <PaywallContextuel {...PROPS}>
        <span>Ouvrir</span>
      </PaywallContextuel>,
    );

    fireEvent.click(screen.getByText("Ouvrir"));

    expect(screen.getByText("Cette feature est en premium")).toBeInTheDocument();
    expect(screen.getByText("Description factuelle.")).toBeInTheDocument();
    expect(screen.getByText("Bénéfice un")).toBeInTheDocument();
    expect(screen.getByText("Bénéfice deux")).toBeInTheDocument();
  });

  it("shows the primary CTA linking to /premium with the exact price copy", () => {
    render(
      <PaywallContextuel {...PROPS}>
        <span>Ouvrir</span>
      </PaywallContextuel>,
    );

    fireEvent.click(screen.getByText("Ouvrir"));

    expect(
      screen.getByRole("link", { name: /passer en premium — 10,99 €\/mois/i }),
    ).toHaveAttribute("href", "/premium");
  });

  it('never crie ("DERNIÈRE CHANCE") nor culpabilise ("tu rates")', () => {
    render(
      <PaywallContextuel {...PROPS}>
        <span>Ouvrir</span>
      </PaywallContextuel>,
    );

    fireEvent.click(screen.getByText("Ouvrir"));

    expect(screen.queryByText(/dernière chance/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/tu rates/i)).not.toBeInTheDocument();
  });

  it('marks the feature as seen on "Plus tard" and skips the sheet next time', () => {
    render(
      <PaywallContextuel {...PROPS}>
        <span>Ouvrir</span>
      </PaywallContextuel>,
    );

    fireEvent.click(screen.getByText("Ouvrir"));
    fireEvent.click(screen.getByRole("button", { name: /plus tard/i }));

    expect(screen.queryByText("Cette feature est en premium")).not.toBeInTheDocument();
    expect(sessionStorage.getItem("paywall_seen_test-feature")).toBe("1");
  });
});
