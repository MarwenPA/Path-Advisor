/**
 * <MobileNav> tests — Story 1.15.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { MobileNav } from "./mobile-nav";

let pathname = "/accueil";
vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/api/auth", () => ({
  logoutUser: vi.fn(),
}));

describe("MobileNav", () => {
  it("renders a bottom tab bar for a role with >= 2 nav items (student)", () => {
    pathname = "/accueil";
    render(<MobileNav role="student" email="sarah@ex.test" />);

    const nav = screen.getByRole("navigation", { name: /navigation principale/i });
    expect(nav).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /accueil/i })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /mes métiers/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /mes paris/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /premium/i })).toBeInTheDocument();
    // No page-title header for the tab-bar shape.
    expect(screen.queryByRole("banner")).not.toBeInTheDocument();
  });

  it("renders a sticky header (no tab bar) for a role with < 2 nav items (parent)", () => {
    pathname = "/parent";
    render(<MobileNav role="parent" email="martin@ex.test" />);

    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByText("Tableau de bord")).toBeInTheDocument();
  });

  it("shows the account menu trigger on both shapes", () => {
    render(<MobileNav role="student" email="sarah@ex.test" />);
    expect(screen.getByRole("button", { name: /mon compte/i })).toBeInTheDocument();
  });

  it("falls back to a generic title when the current path matches no nav item", () => {
    pathname = "/parametres/confidentialite";
    render(<MobileNav role="parent" email="martin@ex.test" />);
    expect(screen.getByText("Path Advisor")).toBeInTheDocument();
  });
});
