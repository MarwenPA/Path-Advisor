/*
 * Lightweight analytics surface — Stories 2.8 (ScenarioLoader) & 2.9
 * (GracefulFallback).
 *
 * MVP has no shipped analytics SDK yet (no PostHog / Plausible / Segment).
 * Until one lands, we expose a typed `track(event)` that emits via
 * `console.info` in development and is a no-op in production. Once a tracker
 * arrives, swap the body of `track()` — every emit site already passes a
 * discriminated union, so the migration is type-checked end-to-end.
 *
 * The discriminated `AnalyticsEvent` union exists precisely so a future
 * tracker integration cannot drift from what components actually emit:
 * adding a new event here forces every consumer to handle it.
 */

export type ScenarioLoaderContext = "ocr" | "reco" | "export" | "payment" | "generic";

export type GracefulFallbackContext =
  | "ocr"
  | "payment"
  | "school_send"
  | "network"
  | "generic";

export type AnalyticsEvent =
  // ScenarioLoader (Story 2.8 AC3 / AC4 / AC5)
  | {
      name: "scenario_loader_completed";
      context: ScenarioLoaderContext;
      actual_seconds: number;
      estimated_seconds: number;
    }
  | {
      name: "scenario_loader_estimation_exceeded";
      context: ScenarioLoaderContext;
      estimated_seconds: number;
      actual_seconds_at_warning: number;
    }
  | {
      name: "scenario_loader_errored";
      context: ScenarioLoaderContext;
      actual_seconds: number;
    }
  // GracefulFallback (Story 2.9 AC7)
  | {
      name: "graceful_fallback_shown";
      context: GracefulFallbackContext;
      title: string;
      has_tertiary: boolean;
    }
  | {
      name: "graceful_fallback_primary_clicked";
      context: GracefulFallbackContext;
      primary_label: string;
      seconds_since_shown: number;
    }
  | {
      name: "graceful_fallback_secondary_clicked";
      context: GracefulFallbackContext;
      secondary_label: string;
      seconds_since_shown: number;
    }
  | {
      name: "graceful_fallback_tertiary_clicked";
      context: GracefulFallbackContext;
      tertiary_label: string;
      seconds_since_shown: number;
    };

type Tracker = (event: AnalyticsEvent) => void;

let trackerOverride: Tracker | null = null;

/**
 * Test seam — replace the emitter with a spy. Pass `null` to restore the
 * default (dev console / prod no-op). Production code never calls this.
 */
export function setAnalyticsTracker(tracker: Tracker | null): void {
  trackerOverride = tracker;
}

export function track(event: AnalyticsEvent): void {
  if (trackerOverride) {
    trackerOverride(event);
    return;
  }
  if (process.env.NODE_ENV !== "production") {
    console.info("[analytics]", event.name, event);
  }
}
