import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ProgressDots } from "./progress-dots";

describe("ProgressDots", () => {
  it("renders 3 dots with the current step marked aria-current=step", () => {
    render(<ProgressDots current={2} />);
    const dots = screen.getAllByRole("button");
    expect(dots).toHaveLength(3);
    expect(dots[1]).toHaveAttribute("aria-current", "step");
    expect(dots[0]).not.toHaveAttribute("aria-current");
    expect(dots[2]).not.toHaveAttribute("aria-current");
  });

  it("makes past dots clickable when onJumpTo is provided", () => {
    const onJumpTo = vi.fn();
    render(<ProgressDots current={3} onJumpTo={onJumpTo} />);
    const [dot1, dot2, dot3] = screen.getAllByRole("button");
    expect(dot1).not.toBeDisabled();
    expect(dot2).not.toBeDisabled();
    expect(dot3).toBeDisabled(); // current — not actionable
    fireEvent.click(dot1!);
    expect(onJumpTo).toHaveBeenCalledWith(1);
  });

  it("disables every dot when onJumpTo is omitted", () => {
    render(<ProgressDots current={2} />);
    const dots = screen.getAllByRole("button");
    dots.forEach((dot) => expect(dot).toBeDisabled());
  });

  it("exposes per-step SR labels", () => {
    render(<ProgressDots current={1} />);
    expect(screen.getByRole("button", { name: /étape 1 sur 3 : passions/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /étape 2 sur 3 : valeurs/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /étape 3 sur 3 : centres d'intérêt/i }),
    ).toBeInTheDocument();
  });
});
