import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// Mock next/navigation for useRouter
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Mock GracefulFallback component
vi.mock("@/components/ui/graceful-fallback", () => ({
  GracefulFallback: ({
    primary,
    secondary,
    tertiary,
  }: {
    primary: { label: string; onClick: () => void };
    secondary?: { label: string; onClick: () => void };
    tertiary?: { label: string; onClick: () => void };
  }) => (
    <div>
      <button onClick={primary.onClick}>{primary.label}</button>
      {secondary && <button onClick={secondary.onClick}>{secondary.label}</button>}
      {tertiary && <button onClick={tertiary.onClick}>{tertiary.label}</button>}
    </div>
  ),
}));

// Mock analytics
vi.mock("@/lib/analytics/events", () => ({ track: vi.fn() }));

import { OCRGracefulFallback } from "../ocr-graceful-fallback";

describe("OCRGracefulFallback — AC7", () => {
  it("renders 2 primary CTAs (manual + retry)", () => {
    render(<OCRGracefulFallback onManual={vi.fn()} onRetry={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    // At minimum: manual and retry (no CTA should be visually dominant over the other)
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it("calls onManual when manual CTA clicked", async () => {
    const onManual = vi.fn();
    render(<OCRGracefulFallback onManual={onManual} onRetry={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /main|saisir/i }));
    expect(onManual).toHaveBeenCalled();
  });

  it("calls onRetry when retry CTA clicked", async () => {
    const onRetry = vi.fn();
    render(<OCRGracefulFallback onManual={vi.fn()} onRetry={onRetry} />);
    await userEvent.click(screen.getByRole("button", { name: /réessayer|retry/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("no CTA is visually marked as 'recommended'", () => {
    render(<OCRGracefulFallback onManual={vi.fn()} onRetry={vi.fn()} />);
    expect(screen.queryByText(/recommand/i)).toBeNull();
  });
});
