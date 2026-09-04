/**
 * <AccountMenu> tests — Story 1.15.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { AccountMenu } from "./account-menu";

const routerMock = { push: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const logoutMock = vi.fn();
vi.mock("@/lib/api/auth", () => ({
  logoutUser: (...args: unknown[]) => logoutMock(...args),
}));

beforeEach(() => {
  routerMock.push.mockClear();
  logoutMock.mockReset();
  logoutMock.mockResolvedValue({ detail: "ok" });
});

describe("AccountMenu", () => {
  it("is closed by default and opens on trigger click", () => {
    render(<AccountMenu email="sarah@ex.test" />);
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    expect(screen.getByRole("menu")).toBeInTheDocument();
  });

  it("shows Paramètres + Déconnexion in the menu", () => {
    render(<AccountMenu email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));

    expect(screen.getByRole("menuitem", { name: /paramètres/i })).toHaveAttribute(
      "href",
      "/parametres/confidentialite",
    );
    expect(screen.getByRole("menuitem", { name: /déconnexion/i })).toBeInTheDocument();
  });

  it("closes on Escape and returns focus to the trigger", () => {
    render(<AccountMenu email="sarah@ex.test" />);
    const trigger = screen.getByRole("button", { name: /sarah@ex.test/i });
    fireEvent.click(trigger);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
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
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.pointerDown(screen.getByRole("button", { name: "outside" }));
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("calls logoutUser() then redirects to /auth/login", async () => {
    render(<AccountMenu email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /déconnexion/i }));

    await waitFor(() => expect(logoutMock).toHaveBeenCalledTimes(1));
    expect(routerMock.push).toHaveBeenCalledWith("/auth/login");
  });

  it("still redirects to /auth/login when logoutUser() rejects", async () => {
    logoutMock.mockRejectedValue(new Error("network down"));
    render(<AccountMenu email="sarah@ex.test" />);
    fireEvent.click(screen.getByRole("button", { name: /sarah@ex.test/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /déconnexion/i }));

    await waitFor(() => expect(routerMock.push).toHaveBeenCalledWith("/auth/login"));
  });

  it("compact variant hides the visible email but keeps it accessible", () => {
    render(<AccountMenu email="sarah@ex.test" variant="compact" />);
    expect(screen.getByText(/mon compte \(sarah@ex\.test\)/i)).toHaveClass("sr-only");
  });
});
