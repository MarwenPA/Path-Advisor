/**
 * <MobileNav> tests — Story 1.15.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { MobileNav } from "./mobile-nav";

let pathname = "/accueil";
vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ replace: vi.fn(), refresh: vi.fn() }),
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
    expect(screen.getByRole("link", { name: /mon profil/i })).toBeInTheDocument();
    // No page-title header for the tab-bar shape.
    expect(screen.queryByRole("banner")).not.toBeInTheDocument();
  });

  it("the tab-bar's account menu opens UPWARD (it sits in a fixed bottom bar)", () => {
    pathname = "/accueil";
    render(<MobileNav role="student" email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /mon compte/i }));
    expect(screen.getByTestId("account-menu-popover").className).toContain("bottom-full");
  });

  it("renders a sticky header (no tab bar) for a role with < 2 nav items (parent)", () => {
    pathname = "/parent";
    render(<MobileNav role="parent" email="martin@ex.test" />);

    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByText("Tableau de bord")).toBeInTheDocument();
  });

  it("header shape still links to the role's single item (regression: used to only show the account icon)", () => {
    pathname = "/parametres/confidentialite";
    render(<MobileNav role="parent" email="martin@ex.test" />);

    expect(screen.getByRole("link", { name: "Tableau de bord" })).toHaveAttribute(
      "href",
      "/parent",
    );
  });

  it("header shape renders path_admin's Admin item as an external link", () => {
    pathname = "/parametres/confidentialite";
    render(<MobileNav role="path_admin" email="admin@ex.test" />);

    const adminLink = screen.getByRole("link", { name: "Admin" });
    expect(adminLink).toHaveAttribute("href", "/admin/");
    expect(adminLink).toHaveAttribute("target", "_blank");
    expect(adminLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("header shape's account menu opens downward", () => {
    pathname = "/parent";
    render(<MobileNav role="parent" email="martin@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /mon compte/i }));
    expect(screen.getByTestId("account-menu-popover").className).toContain("top-full");
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
