import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithIntl } from "@/test/render-with-intl";

import { TrustSection } from "./trust-section";

describe("TrustSection", () => {
  it("reassures on RGPD/free-to-start and links to the legal page", () => {
    renderWithIntl(<TrustSection />);

    expect(
      screen.getByRole("heading", { level: 2, name: /gratuit pour commencer/i }),
    ).toBeInTheDocument();

    const legalLink = screen.getByRole("link", { name: /confidentialité/i });
    expect(legalLink).toHaveAttribute("href", "/legal/rgpd");
  });

  it("lists three reassurance points and repeats the auth CTAs", () => {
    renderWithIntl(<TrustSection />);

    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByRole("link", { name: /créer un compte/i })).toHaveAttribute(
      "href",
      "/auth/signup",
    );
    expect(screen.getByRole("link", { name: /se connecter/i })).toHaveAttribute(
      "href",
      "/auth/login",
    );
  });
});
