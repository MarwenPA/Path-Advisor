/**
 * Story 8.9 — RUM reporter tests.
 *
 * The privacy-critical behaviours are pinned here: authenticated paths are
 * never queued, the beacon carries a page TYPE (never a pathname), and the
 * flush sends `credentials: "omit"`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { __resetQueueForTests, flushQueue, pathnameToPageType, queueVital } from "./rum";

beforeEach(() => {
  __resetQueueForTests();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
  // jsdom has matchMedia only when mocked.
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockReturnValue({ matches: true }), // "mobile"
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("pathnameToPageType", () => {
  it.each([
    ["/", "home"],
    ["/metiers/technicien-aeronautique", "metier_fiche"],
    ["/formations/lycee-pro-aviation", "formation_fiche"],
    ["/devenir-infirmier", "devenir_landing"],
    ["/3eme/quel-bac-pour-infirmier", "niveau_landing"],
    ["/terminale-pro/quel-bac-pour-technicien-aeronautique", "niveau_landing"],
  ] as const)("%s → %s", (pathname, expected) => {
    expect(pathnameToPageType(pathname)).toBe(expected);
  });

  it.each([
    "/mes-metiers",
    "/parametres/confidentialite",
    "/parent/enfants/abc/metiers/x",
    "/metiers", // authenticated catalog, not the public fiche
    "/metiers/slug/extra",
    "/auth/login",
    "/seconde/quel-bac-pour-x", // niveau outside the closed set
  ])("authenticated/unknown path %s → null (never reported)", (pathname) => {
    expect(pathnameToPageType(pathname)).toBeNull();
  });
});

describe("queueVital + flushQueue", () => {
  it("batches public-page metrics and flushes one anonymous request", () => {
    queueVital({ name: "LCP", value: 2100, rating: "good" }, "/metiers/x");
    queueVital({ name: "CLS", value: 0.02, rating: "good" }, "/metiers/x");
    flushQueue();

    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/rum/vitals/");
    expect(init.keepalive).toBe(true);
    // Privacy: no cookie may travel with the beacon, even logged in.
    expect(init.credentials).toBe("omit");
    const payload = JSON.parse(String(init.body));
    expect(payload.vitals).toHaveLength(2);
    // Page TYPE only — never the pathname.
    expect(payload.vitals[0]).toMatchObject({
      metric: "LCP",
      page_type: "metier_fiche",
      device: "mobile",
    });
    expect(JSON.stringify(payload)).not.toContain("/metiers/x");
  });

  it("drops metrics from non-public paths and unknown metric names", () => {
    queueVital({ name: "LCP", value: 900 }, "/mes-metiers");
    queueVital({ name: "NOT_A_METRIC", value: 1 }, "/metiers/x");
    flushQueue();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("caps the queue at the server's batch limit", () => {
    for (let i = 0; i < 15; i++) queueVital({ name: "LCP", value: i }, "/metiers/x");
    const drained = __resetQueueForTests();
    expect(drained).toHaveLength(10);
  });

  it("clears the queue after flushing (no double-send on pagehide + visibilitychange)", () => {
    queueVital({ name: "TTFB", value: 50 }, "/");
    flushQueue();
    flushQueue();
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
