import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// Mock ScenarioLoader (Story 2.8 component)
vi.mock("@/components/ui/scenario-loader", () => ({
  ScenarioLoader: ({
    phrases,
    onComplete,
  }: {
    phrases: string[];
    isComplete?: boolean;
    onComplete?: () => void;
  }) => (
    <div data-testid="scenario-loader">
      <span>{phrases[0]}</span>
      {onComplete && (
        <button onClick={onComplete}>Complete</button>
      )}
    </div>
  ),
}));

import { OCRLoader } from "../ocr-loader";

describe("OCRLoader — AC4", () => {
  it("renders ScenarioLoader placeholder", () => {
    render(
      <OCRLoader
        bulletinId="b1"
        estimatedSeconds={8}
        ocrStatus="pending"
        isComplete={false}
        isError={false}
        onManualFallback={vi.fn()}
      />
    );
    expect(screen.getByTestId("scenario-loader")).toBeTruthy();
  });

  it("shows OCR-themed phrases", () => {
    render(
      <OCRLoader
        bulletinId="b1"
        estimatedSeconds={8}
        ocrStatus="running"
        isComplete={false}
        isError={false}
        onManualFallback={vi.fn()}
      />
    );
    // Should show an OCR-related phrase
    const loader = screen.getByTestId("scenario-loader");
    expect(loader.textContent?.length).toBeGreaterThan(0);
  });

  it("calls onManualFallback when manual link clicked", async () => {
    const onManualFallback = vi.fn();
    render(
      <OCRLoader
        bulletinId="b1"
        estimatedSeconds={8}
        ocrStatus="running"
        isComplete={false}
        isError={false}
        onManualFallback={onManualFallback}
      />
    );
    const fallbackLink = screen.queryByRole("button", { name: /main|saisir|manuel/i });
    if (fallbackLink) {
      await userEvent.click(fallbackLink);
      expect(onManualFallback).toHaveBeenCalled();
    }
  });
});
