import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithIntl } from "@/test/render-with-intl";

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("links the wordmark to the home page and exposes the login CTA", () => {
    renderWithIntl(<SiteHeader />);

    expect(screen.getByRole("link", { name: /path-advisor, accueil/i })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByRole("link", { name: /se connecter/i })).toHaveAttribute(
      "href",
      "/auth/login",
    );
  });
});
