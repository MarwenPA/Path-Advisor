/**
 * Story 8.9 — RUM bootstrap (Next.js `instrumentation-client` convention).
 *
 * Deliberately NOT a React component: the first version was a client
 * component in the root layout, and the Core Web Vitals gate measured it
 * adding ~40ms of simulated LCP on the tightest page (a root-layout client
 * boundary rides every page's critical path). Here the collector's chunk is
 * fetched at browser IDLE, after `load` — zero critical-path bytes — and
 * web-vitals' buffered PerformanceObservers still capture LCP/FCP/TTFB
 * despite the late subscription.
 */

function startRum(): void {
  const boot = () => {
    void import("@/lib/telemetry/rum").then((m) => m.initRum());
  };
  // 1200ms is a DEADLINE for requestIdleCallback, not a delay — on an idle
  // machine the callback fires within ~100ms of `load` (verified via
  // headless-Chrome console markers). Kept short so even quick bounces get
  // a subscription in time. Debugging honesty note: an earlier version of
  // this comment blamed a 5s deadline for losing beacons; the real culprit
  // was the test harness itself (probe served on :3200, a port absent from
  // Django's CORS_ALLOWED_ORIGINS — the beacon was CORS-blocked). The
  // deadline value was never the problem.
  if ("requestIdleCallback" in window) {
    requestIdleCallback(boot, { timeout: 1200 });
  } else {
    setTimeout(boot, 1200);
  }
}

if (document.readyState === "complete") {
  startRum();
} else {
  window.addEventListener("load", startRum, { once: true });
}
