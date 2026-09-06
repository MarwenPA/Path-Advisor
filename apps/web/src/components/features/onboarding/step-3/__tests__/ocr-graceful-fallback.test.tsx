import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// Mock next/navigation for useRouter
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Mock GracefulFallback component — prop names match the real component's
// `primaryAction`/`secondaryAction`/`tertiaryLink` (this mock had drifted).
vi.mock("@/components/ui/graceful-fallback", () => ({
  GracefulFallback: ({
    primaryAction,
    secondaryAction,
    tertiaryLink,
  }: {
    primaryAction: { label: string; onClick: () => void };
    secondaryAction?: { label: string; onClick: () => void };
    tertiaryLink?: { label: string; onClick: () => void };
  }) => (
    <div>
      <button onClick={primaryAction.onClick}>{primaryAction.label}</button>
      {secondaryAction && (
        <button onClick={secondaryAction.onClick}>{secondaryAction.label}</button>
      )}
      {tertiaryLink && <button onClick={tertiaryLink.onClick}>{tertiaryLink.label}</button>}
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
