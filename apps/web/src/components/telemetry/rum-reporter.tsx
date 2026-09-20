"use client";

import { useReportWebVitals } from "next/web-vitals";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

/**
 * Story 8.9 — anonymous Real User Monitoring of Core Web Vitals.
 *
 * Every perf budget in `lighthouserc.json` is calibrated against a
 * SIMULATED metric; this component is the field instrument that gap
 * lacked (it allowed two bad threshold calls during Epic 7).
 *
 * Privacy (the app serves minors — GDPR, AC4):
 * - PUBLIC pages only: `pathnameToPageType` is a closed mapping, and
 *   anything it does not recognise — the whole authenticated space — is
 *   never queued;
 * - the beacon carries a page TYPE, never a pathname (a slug could reveal
 *   a niche interest, a type cannot), and no id of any kind;
 * - `credentials: "omit"` so even a logged-in student's beacon travels
 *   without a session cookie — the backend additionally processes it with
 *   `authentication_classes = []` (anonymity at both ends);
 * - the ingest table has no user/IP/URL column at all (see
 *   `apps/api/apps/telemetry/models.py` — privacy by construction).
 *
 * Transport: metrics are queued as web-vitals reports them and flushed in
 * ONE batched request when the page is hidden/unloaded, via
 * `fetch(keepalive)` rather than `sendBeacon` — sendBeacon cannot carry
 * `application/json` without CORS trouble, keepalive can.
 */

const PAGE_TYPES = {
  home: /^\/$/,
  metier_fiche: /^\/metiers\/[^/]+$/,
  formation_fiche: /^\/formations\/[^/]+$/,
  devenir_landing: /^\/devenir-[^/]+$/,
  niveau_landing:
    /^\/(3eme|terminale-generale|terminale-technologique|terminale-pro)\/quel-bac-pour-[^/]+$/,
} as const;

export type RumPageType = keyof typeof PAGE_TYPES;

export function pathnameToPageType(pathname: string): RumPageType | null {
  for (const [type, re] of Object.entries(PAGE_TYPES) as [RumPageType, RegExp][]) {
    if (re.test(pathname)) return type;
  }
  return null;
}

interface QueuedVital {
  metric: string;
  value: number;
  rating: string;
  page_type: RumPageType;
  device: "mobile" | "desktop";
  connection: string;
}

// Server-side cap is MAX_BATCH=10; one page view emits at most 5 metrics.
const MAX_QUEUE = 10;
const REPORTED_METRICS = new Set(["LCP", "CLS", "INP", "TTFB", "FCP"]);
const KNOWN_CONNECTIONS = new Set(["slow-2g", "2g", "3g", "4g"]);

let queue: QueuedVital[] = [];

function currentDevice(): "mobile" | "desktop" {
  return window.matchMedia("(max-width: 767px)").matches ? "mobile" : "desktop";
}

function currentConnection(): string {
  const nav = navigator as Navigator & { connection?: { effectiveType?: string } };
  const type = nav.connection?.effectiveType;
  return type && KNOWN_CONNECTIONS.has(type) ? type : "unknown";
}

export function queueVital(
  metric: { name: string; value: number; rating?: string },
  pathname: string,
): void {
  const pageType = pathnameToPageType(pathname);
  if (!pageType || !REPORTED_METRICS.has(metric.name)) return;
  if (queue.length >= MAX_QUEUE) return;
  queue.push({
    metric: metric.name,
    value: metric.value,
    rating: metric.rating ?? "good",
    page_type: pageType,
    device: currentDevice(),
    connection: currentConnection(),
  });
}

export function flushQueue(): void {
  if (queue.length === 0) return;
  const body = JSON.stringify({ vitals: queue });
  queue = [];
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  // keepalive lets the request outlive the page; errors are irrelevant —
  // losing a beacon must never surface to the user.
  fetch(`${base}/api/v1/rum/vitals/`, {
    method: "POST",
    keepalive: true,
    credentials: "omit",
    headers: { "Content-Type": "application/json" },
    body,
  }).catch(() => {});
}

/** Test seam — the queue is module state. */
export function __resetQueueForTests(): QueuedVital[] {
  const drained = queue;
  queue = [];
  return drained;
}

export function RumReporter() {
  const pathname = usePathname();

  useReportWebVitals((metric) => {
    queueVital(metric, pathname ?? window.location.pathname);
  });

  useEffect(() => {
    const onHidden = () => {
      if (document.visibilityState === "hidden") flushQueue();
    };
    document.addEventListener("visibilitychange", onHidden);
    // Safari does not reliably fire visibilitychange on unload.
    window.addEventListener("pagehide", flushQueue);
    return () => {
      document.removeEventListener("visibilitychange", onHidden);
      window.removeEventListener("pagehide", flushQueue);
    };
  }, []);

  return null;
}
