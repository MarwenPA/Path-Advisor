import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";

import { ScenarioLoader } from "./scenario-loader";
import { setAnalyticsTracker, type AnalyticsEvent } from "@/lib/analytics/events";

type ChangeListener = (event: { matches: boolean }) => void;

function mockMatchMedia(reduced: boolean) {
  const listeners = new Set<ChangeListener>();
  const mq = {
    matches: reduced,
    addEventListener: (_: string, listener: ChangeListener) => listeners.add(listener),
    removeEventListener: (_: string, listener: ChangeListener) => listeners.delete(listener),
  };
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => mq),
  );
}

describe("ScenarioLoader", () => {
  let events: AnalyticsEvent[];

  beforeEach(() => {
    events = [];
    setAnalyticsTracker((event) => events.push(event));
    mockMatchMedia(false);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    setAnalyticsTracker(null);
  });

  it("renders the first phrase, generic icon, bar at 0%, and estimation copy", () => {
    render(<ScenarioLoader phrases={["First", "Second"]} estimatedSeconds={10} />);

    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("First");
    expect(screen.getByText(/Estimation : ~10 secondes/)).toBeInTheDocument();
    const bar = screen.getByTestId("scenario-loader-bar").querySelector("div");
    expect(bar?.getAttribute("style")).toContain("width: 0%");
    expect(screen.getByRole("status", { name: /chargement en cours/i })).toBeInTheDocument();
  });

  it("uses the context-specific SR label", () => {
    render(
      <ScenarioLoader
        phrases={["A", "B"]}
        estimatedSeconds={20}
        context="ocr"
      />,
    );
    expect(
      screen.getByRole("status", { name: /analyse des bulletins en cours/i }),
    ).toBeInTheDocument();
  });

  it("advances to the next phrase after the clamped duration", () => {
    render(
      <ScenarioLoader
        phrases={["A", "B", "C"]}
        estimatedSeconds={15}
        context="reco"
      />,
    );
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("A");
    // 15 s / 3 phrases = 5 s per phrase (within clamp 4-12 s).
    act(() => {
      vi.advanceTimersByTime(5_000);
    });
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("B");
    act(() => {
      vi.advanceTimersByTime(5_000);
    });
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("C");
  });

  it("clamps phrase duration to a 4-second minimum even when phrases.length >> estimatedSeconds", () => {
    render(
      <ScenarioLoader
        phrases={["A", "B", "C", "D", "E", "F"]}
        estimatedSeconds={5}
        context="reco"
      />,
    );
    // 5 / 6 = 0.83 s → clamped to 4 s plancher.
    act(() => {
      vi.advanceTimersByTime(3_999);
    });
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("A");
    act(() => {
      vi.advanceTimersByTime(2);
    });
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("B");
  });

  it("freezes on the last phrase — no loop back to phrase 0", () => {
    render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} context="reco" />,
    );
    act(() => {
      vi.advanceTimersByTime(60_000);
    });
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("B");
  });

  it("shows the overrun warning after estimatedSeconds and emits a single analytics event", () => {
    render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={3} context="ocr" />,
    );
    expect(screen.queryByTestId("scenario-loader-warning")).not.toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3_000);
    });
    expect(screen.getByTestId("scenario-loader-warning")).toBeInTheDocument();
    expect(
      screen.getByText(/Ça prend un peu plus de temps que prévu, on continue\./),
    ).toBeInTheDocument();

    // Idempotent — even after a long extra wait, only one event was emitted.
    act(() => {
      vi.advanceTimersByTime(30_000);
    });
    const overrunEvents = events.filter(
      (e) => e.name === "scenario_loader_estimation_exceeded",
    );
    expect(overrunEvents).toHaveLength(1);
    expect(overrunEvents[0]).toMatchObject({ context: "ocr", estimated_seconds: 3 });
  });

  it("renders the fallback button only when `onFallback` is provided", () => {
    const onFallback = vi.fn();
    render(
      <ScenarioLoader
        phrases={["A", "B"]}
        estimatedSeconds={2}
        context="ocr"
        onFallback={onFallback}
        fallbackLabel="Saisir à la main"
      />,
    );
    act(() => {
      vi.advanceTimersByTime(2_000);
    });
    const button = screen.getByRole("button", { name: "Saisir à la main" });
    fireEvent.click(button);
    expect(onFallback).toHaveBeenCalledTimes(1);
  });

  it("snaps the bar to 100 % and emits `scenario_loader_completed` when isComplete flips true", () => {
    const { rerender } = render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} context="reco" />,
    );
    act(() => {
      vi.advanceTimersByTime(2_000);
    });
    rerender(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} context="reco" isComplete />,
    );
    const bar = screen.getByTestId("scenario-loader-bar").querySelector("div");
    expect(bar?.getAttribute("style")).toContain("width: 100%");
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("B");
    expect(screen.queryByTestId("scenario-loader-particle")).not.toBeInTheDocument();

    const completed = events.filter((e) => e.name === "scenario_loader_completed");
    expect(completed).toHaveLength(1);
    expect(completed[0]).toMatchObject({ context: "reco", estimated_seconds: 10 });
  });

  it("fades out and emits `scenario_loader_errored` when isError flips true (isError beats isComplete)", () => {
    const { rerender, container } = render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} context="payment" />,
    );
    rerender(
      <ScenarioLoader
        phrases={["A", "B"]}
        estimatedSeconds={10}
        context="payment"
        isComplete
        isError
      />,
    );
    const section = container.querySelector('section[role="status"]');
    expect(section?.className).toContain("opacity-0");

    const errored = events.filter((e) => e.name === "scenario_loader_errored");
    const completed = events.filter((e) => e.name === "scenario_loader_completed");
    expect(errored).toHaveLength(1);
    expect(completed).toHaveLength(0);
  });

  it("does not render the particle when prefers-reduced-motion is set", () => {
    vi.unstubAllGlobals();
    mockMatchMedia(true);
    render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} context="reco" />,
    );
    expect(screen.queryByTestId("scenario-loader-particle")).not.toBeInTheDocument();
  });

  it("clears all timers on unmount — no leak", () => {
    const { unmount } = render(
      <ScenarioLoader phrases={["A", "B", "C"]} estimatedSeconds={30} context="ocr" />,
    );
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });

  it("resets to phrase 0 when the `phrases` array reference changes", () => {
    const { rerender } = render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} />,
    );
    act(() => {
      vi.advanceTimersByTime(5_000);
    });
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("B");
    rerender(<ScenarioLoader phrases={["X", "Y"]} estimatedSeconds={10} />);
    expect(screen.getByTestId("scenario-loader-phrase")).toHaveTextContent("X");
  });
});
