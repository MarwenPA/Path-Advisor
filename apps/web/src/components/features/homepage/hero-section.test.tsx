import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithIntl } from "@/test/render-with-intl";

import { HeroSection } from "./hero-section";

describe("HeroSection", () => {
  it("renders the single page h1 and both auth CTAs", () => {
    renderWithIntl(<HeroSection />);

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();

    const signup = screen.getByRole("link", { name: /créer un compte/i });
    expect(signup).toHaveAttribute("href", "/auth/signup");

    const login = screen.getByRole("link", { name: /se connecter/i });
    expect(login).toHaveAttribute("href", "/auth/login");
  });
});
