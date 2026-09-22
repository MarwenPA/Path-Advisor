/**
 * Story 8.9 — anonymous Real User Monitoring of Core Web Vitals.
 *
 * Framework-free ON PURPOSE, and loaded at browser idle from
 * `instrumentation-client.ts` — the first version of this was a client
 * component mounted in the root layout, and the CWV gate caught it adding
 * ~40ms of simulated LCP on `/metiers/{slug}` (a client boundary in the
 * root layout puts its chunk on every page's critical path). The measuring
 * instrument must not distort the measurement: this module now costs ZERO
 * critical-path bytes — web-vitals' PerformanceObservers are buffered, so
 * subscribing after `load`+idle still captures LCP/FCP/TTFB.
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
 * Transport: one batched `fetch(keepalive)` on pagehide/visibility-hidden —
 * `sendBeacon` cannot carry `application/json` without CORS trouble.
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

/**
 * Subscribe web-vitals (buffered observers — late subscription is fine)
 * and arm the pagehide flush. Called once, at idle, from
 * `instrumentation-client.ts`.
 */
export async function initRum(): Promise<void> {
  const { onCLS, onFCP, onINP, onLCP, onTTFB } = await import("web-vitals");
  const report = (metric: { name: string; value: number; rating?: string }) =>
    queueVital(metric, window.location.pathname);
  onLCP(report);
  onCLS(report);
  onINP(report);
  onTTFB(report);
  onFCP(report);

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushQueue();
  });
  // Safari does not reliably fire visibilitychange on unload.
  window.addEventListener("pagehide", flushQueue);
}
