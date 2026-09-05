/**
 * <AccountMenu> tests — Story 1.15.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { AccountMenu } from "./account-menu";

const routerMock = { replace: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const logoutMock = vi.fn();
vi.mock("@/lib/api/auth", () => ({
  logoutUser: (...args: unknown[]) => logoutMock(...args),
}));

beforeEach(() => {
  routerMock.replace.mockClear();
  routerMock.refresh.mockClear();
  logoutMock.mockReset();
  logoutMock.mockResolvedValue({ detail: "ok" });
});

describe("AccountMenu", () => {
  it("is closed by default and opens on trigger click", () => {
    render(<AccountMenu email="sarah@ex.test" />);
    expect(screen.queryByTestId("account-menu-popover")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    expect(screen.getByTestId("account-menu-popover")).toBeInTheDocument();
  });

  it("shows Paramètres + Déconnexion in the popover", () => {
    render(<AccountMenu email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));

    expect(screen.getByRole("link", { name: /paramètres/i })).toHaveAttribute(
      "href",
      "/parametres/confidentialite",
    );
    expect(screen.getByRole("button", { name: /déconnexion/i })).toBeInTheDocument();
  });

  it("closes on Escape and returns focus to the trigger", () => {
    render(<AccountMenu email="sarah@ex.test" />);
    const trigger = screen.getByRole("button", { name: /sarah@ex.test/i });
    fireEvent.click(trigger);
    expect(screen.getByTestId("account-menu-popover")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByTestId("account-menu-popover")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("closes on outside click", () => {
    render(
      <div>
        <AccountMenu email="sarah@ex.test" />
        <button type="button">outside</button>
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    expect(screen.getByTestId("account-menu-popover")).toBeInTheDocument();

    fireEvent.pointerDown(screen.getByRole("button", { name: "outside" }));
    expect(screen.queryByTestId("account-menu-popover")).not.toBeInTheDocument();
  });

  it("calls logoutUser() then replaces the route with /auth/login and refreshes", async () => {
    render(<AccountMenu email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    fireEvent.click(screen.getByRole("button", { name: /déconnexion/i }));

    await waitFor(() => expect(logoutMock).toHaveBeenCalledTimes(1));
    expect(routerMock.replace).toHaveBeenCalledWith("/auth/login");
    expect(routerMock.refresh).toHaveBeenCalledTimes(1);
  });

  it("still redirects to /auth/login when logoutUser() rejects", async () => {
    logoutMock.mockRejectedValue(new Error("network down"));
    render(<AccountMenu email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    fireEvent.click(screen.getByRole("button", { name: /déconnexion/i }));

    await waitFor(() => expect(routerMock.replace).toHaveBeenCalledWith("/auth/login"));
  });

  it("compact variant hides the visible email but keeps it accessible", () => {
    render(<AccountMenu email="sarah@ex.test" variant="compact" />);
    expect(screen.getByText(/mon compte \(sarah@ex\.test\)/i)).toHaveClass("sr-only");
  });

  it('placement="up" opens the popover above the trigger (bottom-full)', () => {
    render(<AccountMenu email="sarah@ex.test" placement="up" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    expect(screen.getByTestId("account-menu-popover").className).toContain("bottom-full");
  });

  it('placement="down" (default) opens the popover below the trigger (top-full)', () => {
    render(<AccountMenu email="sarah@ex.test" variant="compact" />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByTestId("account-menu-popover").className).toContain("top-full");
  });
});
