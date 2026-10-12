import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";

import { renderWithIntl } from "@/test/render-with-intl";

import { HeroSection } from "./hero-section";

describe("HeroSection", () => {
  it("renders the single page h1 and both auth CTAs", () => {
    renderWithIntl(<HeroSection />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Trouve ta voie, étape par étape.",
    );

    const signup = screen.getByRole("link", { name: /créer un compte/i });
    expect(signup).toHaveAttribute("href", "/auth/signup");

    const login = screen.getByRole("link", { name: /se connecter/i });
    expect(login).toHaveAttribute("href", "/auth/login");
  });

  it("lists the three guarantees", () => {
    renderWithIntl(<HeroSection />);

    const guarantees = screen.getByRole("list", { name: /garanties/i });
    expect(within(guarantees).getAllByRole("listitem")).toHaveLength(3);
  });

  it("shows a clearly fictional recommendation example with its explained signals", () => {
    renderWithIntl(<HeroSection />);

    const example = screen.getByRole("complementary", { name: /exemple fictif/i });
    expect(within(example).getByText(/exemple fictif/i)).toBeInTheDocument();
    expect(within(example).getByText(/génie biomédical/i)).toBeInTheDocument();

    const signals = within(example).getByRole("list", { name: /signaux expliqués/i });
    expect(within(signals).getAllByRole("listitem")).toHaveLength(3);
  });
});
