import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "./page";

describe("Home page", () => {
  it("renders the foundation seed greeting with the h1 wired to the design tokens", () => {
    render(<Home />);

    const heading = screen.getByRole("heading", { level: 1, name: /hello path-advisor/i });
    expect(heading).toBeInTheDocument();
    // Token-driven typography must actually be applied on the consumer.
    expect(heading.className).toMatch(/\btext-h1\b/);
    expect(heading.className).toMatch(/\bmd:text-h1-desktop\b/);
  });

  it("exposes the design system showcase as an accessible landmark with three buttons", () => {
    render(<Home />);

    // aria-labelledby + matching h2 ⇒ both should resolve to the same accessible name.
    const region = screen.getByRole("region", { name: /design tokens/i });
    expect(region).toBeInTheDocument();

    const h2 = screen.getByRole("heading", { level: 2, name: /design tokens/i });
    expect(h2).toBeInTheDocument();
    expect(region).toContainElement(h2);

    expect(screen.getByRole("button", { name: /^primary$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^outline$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^secondary$/i })).toBeInTheDocument();
  });
});
