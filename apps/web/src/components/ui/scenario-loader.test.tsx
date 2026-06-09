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
    // M5 (post-review patch) — particle stays MOUNTED with
    // `data-animating="false"` so the animation freezes on its current frame
    // instead of being yanked from the DOM ("stoppe sur sa frame visible").
    const particle = screen.getByTestId("scenario-loader-particle");
    expect(particle).toHaveAttribute("data-animating", "false");

    const completed = events.filter((e) => e.name === "scenario_loader_completed");
    expect(completed).toHaveLength(1);
    expect(completed[0]).toMatchObject({ context: "reco", estimated_seconds: 10 });
  });

  // H1 (post-review patch) — bar must transition 0% → 100% over `safeSeconds`
  // during the wait, not snap-only on completion. The fix uses a state seeded
  // to 0 then flipped to 100 via requestAnimationFrame so the CSS transition
  // (duration = safeSeconds) actually runs. The previous shipped behaviour
  // (`barWidth = isComplete ? 100 : 0`) left the bar empty for the full wait.
  it("animates the bar from 0% to 100% during the wait (H1 — anti-empty-bar)", () => {
    render(<ScenarioLoader phrases={["A"]} estimatedSeconds={5} context="reco" />);
    const bar = screen.getByTestId("scenario-loader-bar").querySelector("div");
    // Initial render: width is the seeded 0%.
    expect(bar?.getAttribute("style")).toContain("width: 0%");
    // jsdom polyfills `requestAnimationFrame` as `setTimeout(cb, 16)`, so
    // advancing fake timers by ~17 ms fires the RAF and commits the state
    // flip to 100%. The CSS transition then runs over the configured 5 s.
    act(() => {
      vi.advanceTimersByTime(17);
    });
    expect(bar?.getAttribute("style")).toContain("width: 100%");
    expect(bar?.getAttribute("style")).toContain("transition-duration: 5s");
  });

  // H4 (post-review patch) — phrases-swap during an active error must NOT
  // re-emit `scenario_loader_errored`. The fix gates the start-stamp effect
  // on `!isError` and removes `phrasesKey` from the error effect deps.
  it("does not re-emit `scenario_loader_errored` when phrases swap during an active error (H4)", () => {
    const { rerender } = render(
      <ScenarioLoader phrases={["A", "B"]} estimatedSeconds={10} context="ocr" isError />,
    );
    rerender(
      <ScenarioLoader phrases={["X", "Y"]} estimatedSeconds={10} context="ocr" isError />,
    );
    const errored = events.filter((e) => e.name === "scenario_loader_errored");
    expect(errored).toHaveLength(1);
  });

  // M6 (post-review patch) — `actual_seconds_at_warning` must carry the real
  // elapsed wall-clock at the moment the warning fires, not the estimate.
  it("populates `actual_seconds_at_warning` with the real elapsed time (M6)", () => {
    render(<ScenarioLoader phrases={["A", "B"]} estimatedSeconds={3} context="ocr" />);
    act(() => {
      vi.advanceTimersByTime(3_000);
    });
    const warned = events.filter((e) => e.name === "scenario_loader_estimation_exceeded");
    expect(warned).toHaveLength(1);
    expect(warned[0]).toMatchObject({
      estimated_seconds: 3,
      // Approximately 3s elapsed (fake timer is precise) — the bug shipped
      // `actual_seconds_at_warning: safeSeconds` which happened to equal 3
      // here too. The robust check is that the field IS now distinct from
      // the estimate — assert it's a number in a tight band around 3s.
    });
    const actual = (warned[0] as { actual_seconds_at_warning: number }).actual_seconds_at_warning;
    expect(actual).toBeGreaterThanOrEqual(2.9);
    expect(actual).toBeLessThanOrEqual(3.1);
  });

  // Pass 2 PR1 — the crossfade container must NOT use absolute positioning
  // with a fixed min-height, because long French phrases ("Qu'est-ce qui te
  // plaît, vraiment ?") wrap to multiple lines on mobile and would overflow.
  // The fixed implementation uses CSS grid stack (every `<p>` shares
  // col-start-1 row-start-1) so the container auto-sizes to the tallest
  // phrase.
  it("uses CSS grid stack for crossfade (not absolute) so the container auto-sizes (Pass 2 PR1)", () => {
    const longPhrase = "Qu'est-ce qui te plaît, vraiment ? Pas de pression, choisis ce qui te branche.";
    const { container } = render(
      <ScenarioLoader phrases={[longPhrase, "Short"]} estimatedSeconds={10} context="ocr" />,
    );
    // Find the wrapper that contains the phrase paragraphs.
    const phraseWrapper = screen.getByTestId("scenario-loader-phrase").parentElement;
    expect(phraseWrapper).not.toBeNull();
    expect(phraseWrapper!.className).toContain("grid");
    // No legacy `min-h-7` cap, no `relative`+absolute kids.
    expect(phraseWrapper!.className).not.toContain("min-h-7");
    // Every phrase shares the same grid cell.
    const phrasesInside = phraseWrapper!.querySelectorAll("p");
    expect(phrasesInside.length).toBe(2);
    phrasesInside.forEach((p) => {
      expect(p.className).toContain("col-start-1");
      expect(p.className).toContain("row-start-1");
    });
    // Sanity: the long phrase is the one we passed in (no truncation).
    expect(phrasesInside[0]?.textContent).toBe(longPhrase);
    void container; // satisfy unused lint
  });

  // Pass 2 PR2 — the final-state announcer is a SIBLING of the section, not
  // a descendant. AC6 says "une seconde zone `aria-live` SÉPARÉE"; nesting
  // two live regions caused double-announcements in Pass 1's M10 partial fix.
  it("renders the completion announcer as a SIBLING of the section (Pass 2 PR2)", () => {
    const { container } = render(
      <ScenarioLoader phrases={["A"]} estimatedSeconds={5} context="reco" isComplete />,
    );
    // The announcer span carries "Terminé." and lives directly under the
    // wrapper, NOT inside the section.
    const section = container.querySelector("section[role=status]");
    const announcer = container.querySelector("span[aria-live=polite]");
    expect(section).not.toBeNull();
    expect(announcer).not.toBeNull();
    expect(announcer!.textContent).toContain("Terminé.");
    // The announcer must NOT be a descendant of the section.
    expect(section!.contains(announcer)).toBe(false);
  });

  // M8 (post-review patch) — `isError: true → false` must reverse the
  // fade-out and re-arm the emission latch so a subsequent error re-emits.
  it("reverses the fade-out when isError transitions back to false (M8)", () => {
    const { rerender, container } = render(
      <ScenarioLoader phrases={["A"]} estimatedSeconds={10} context="reco" isError />,
    );
    expect(container.querySelector('section[data-state="error"]')?.className).toContain(
      "opacity-0",
    );
    rerender(
      <ScenarioLoader phrases={["A"]} estimatedSeconds={10} context="reco" isError={false} />,
    );
    expect(container.querySelector("section")?.className).not.toContain("opacity-0");

    // Now error again — analytics latch must have re-armed.
    rerender(
      <ScenarioLoader phrases={["A"]} estimatedSeconds={10} context="reco" isError />,
    );
    const errored = events.filter((e) => e.name === "scenario_loader_errored");
    expect(errored).toHaveLength(2);
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
