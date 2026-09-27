/**
 * SideFlow — Story 10.6 generic contracts.
 *
 * Contracts: an open banner is a polite status region (never a dialog — the
 * AC is "non-bloquant"), the CTA fires, a closed first render shows nothing,
 * and the true→false transition with `resolvedMessage` shows the resolution
 * toast, which auto-dismisses.
 */
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SideFlow } from "./side-flow";

afterEach(() => {
  vi.useRealTimers();
});

describe("SideFlow", () => {
  it("renders an open banner as a polite status region with message and CTA", async () => {
    const onClick = vi.fn();
    render(
      <SideFlow
        open
        message="Ton parent reçoit l'email."
        cta={{ label: "Relancer mon parent", onClick }}
      />,
    );

    const region = screen.getByRole("status");
    expect(region).toHaveTextContent("Ton parent reçoit l'email.");
    expect(region).toHaveAttribute("aria-live", "polite");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Relancer mon parent" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders nothing when closed from the start (no phantom toast)", () => {
    render(<SideFlow open={false} message="Message" resolvedMessage="Résolu." />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows the resolution toast on the open→closed transition, then auto-dismisses", () => {
    vi.useFakeTimers();
    const { rerender } = render(
      <SideFlow open message="En attente." resolvedMessage="Ton compte est actif." />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("En attente.");

    rerender(
      <SideFlow open={false} message="En attente." resolvedMessage="Ton compte est actif." />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Ton compte est actif.");

    act(() => {
      vi.advanceTimersByTime(6000);
    });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("positions the bottom variant as fixed above the mobile tab bar", () => {
    render(<SideFlow open message="Bas de page." position="bottom" />);
    expect(screen.getByRole("status")).toHaveClass("fixed", "bottom-16", "lg:bottom-0");
  });
});
