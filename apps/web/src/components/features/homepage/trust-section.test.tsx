import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { TrustSection } from "./trust-section";

describe("TrustSection", () => {
  it("reassures on RGPD/free-to-start and links to the legal page", () => {
    render(<TrustSection />);

    expect(
      screen.getByRole("heading", { level: 2, name: /gratuit pour commencer/i }),
    ).toBeInTheDocument();

    const legalLink = screen.getByRole("link", { name: /confidentialité/i });
    expect(legalLink).toHaveAttribute("href", "/legal/rgpd");
  });
});
