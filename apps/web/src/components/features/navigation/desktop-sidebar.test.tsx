/**
 * <DesktopSidebar> tests — Story 1.15.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { DesktopSidebar } from "./desktop-sidebar";

let pathname = "/accueil";
vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ replace: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("@/lib/api/auth", () => ({
  logoutUser: vi.fn(),
}));

describe("DesktopSidebar", () => {
  it("renders the student's nav items with the logo linking home", () => {
    pathname = "/accueil";
    render(<DesktopSidebar role="student" email="sarah@ex.test" />);

    expect(screen.getByRole("link", { name: /path advisor/i })).toHaveAttribute("href", "/accueil");
    expect(screen.getByRole("link", { name: /accueil/i })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /mes métiers/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /mes paris/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /premium/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /mon profil/i })).toBeInTheDocument();
  });

  it("applies the active-item styling classes, not just aria-current", () => {
    pathname = "/accueil";
    render(<DesktopSidebar role="student" email="sarah@ex.test" />);

    expect(screen.getByRole("link", { name: /accueil/i }).className).toEqual(
      expect.stringContaining("border-brand"),
    );
    expect(screen.getByRole("link", { name: /mes métiers/i }).className).not.toContain(
      "border-brand",
    );
  });

  it("marks a nested route as active via prefix match", () => {
    pathname = "/mes-metiers/some-slug";
    render(<DesktopSidebar role="student" email="sarah@ex.test" />);

    expect(screen.getByRole("link", { name: /mes métiers/i })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: /accueil/i })).not.toHaveAttribute("aria-current");
  });

  it("renders no metier item for a role without shipped nav entries", () => {
    pathname = "/parametres/confidentialite";
    render(<DesktopSidebar role="counselor" email="dupont@ex.test" />);

    expect(screen.queryByRole("link", { name: /cohorte/i })).not.toBeInTheDocument();
    // Logo + account menu trigger are still present.
    expect(screen.getByRole("link", { name: /path advisor/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dupont@ex\.test/i })).toBeInTheDocument();
  });

  it("renders path_admin's Admin item as an external link, not a Next <Link>", () => {
    pathname = "/parametres/confidentialite";
    render(<DesktopSidebar role="path_admin" email="admin@ex.test" />);

    const adminLink = screen.getByRole("link", { name: /admin/i });
    expect(adminLink).toHaveAttribute("href", "/admin/");
    expect(adminLink).toHaveAttribute("target", "_blank");
    expect(adminLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders path_admin's logo as an external link too — /admin/ isn't a Next route", () => {
    pathname = "/parametres/confidentialite";
    render(<DesktopSidebar role="path_admin" email="admin@ex.test" />);

    const logoLink = screen.getByRole("link", { name: /path advisor/i });
    expect(logoLink).toHaveAttribute("href", "/admin/");
    expect(logoLink).toHaveAttribute("target", "_blank");
    expect(logoLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("shows the account menu trigger with the user's email", () => {
    render(<DesktopSidebar role="student" email="sarah@ex.test" />);
    expect(screen.getByRole("button", { name: /sarah@ex\.test/i })).toBeInTheDocument();
  });
});
