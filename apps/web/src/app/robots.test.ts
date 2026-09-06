/**
 * `/robots.txt` tests — Story 7.4, hardened by the Epic 7 review
 * (trailing-slash prefixes + staging noindex).
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import robots from "./robots";

describe("robots", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("allows public pages and points to the sitemap", () => {
    const result = robots();
    expect(result.rules).toMatchObject({ userAgent: "*", allow: "/" });
    expect(result.sitemap).toBe("https://path-advisor.fr/sitemap.xml");
  });

  it("disallows every application/admin route prefix", () => {
    const result = robots();
    const disallow = (result.rules as { disallow: string[] }).disallow;
    expect(disallow).toEqual(
      expect.arrayContaining(["/api", "/admin", "/parametres", "/auth", "/schools"]),
    );
  });

  it("uses slash-less prefixes (Epic 7 review: '/parametres/' does not match '/parametres')", () => {
    const result = robots();
    const disallow = (result.rules as { disallow: string[] }).disallow;
    for (const prefix of disallow) {
      expect(prefix.endsWith("/")).toBe(false);
    }
  });

  it("does not disallow the public SEO routes", () => {
    const result = robots();
    const disallow = (result.rules as { disallow: string[] }).disallow;
    const publicPaths = ["/metiers/x", "/formations/x", "/devenir-x", "/3eme/quel-bac-pour-x"];
    for (const path of publicPaths) {
      expect(disallow.some((prefix) => path.startsWith(prefix))).toBe(false);
    }
  });

  it("disallows EVERYTHING on a non-production origin (Epic 7 review: staging noindex)", async () => {
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_SITE_ORIGIN", "https://staging.path-advisor.fr");
    // Re-import so `SITE_ORIGIN` (read at module init) picks up the stub.
    const { default: stagingRobots } = await import("./robots");

    const result = stagingRobots();
    expect(result.rules).toEqual({ userAgent: "*", disallow: "/" });
    expect(result.sitemap).toBeUndefined();
  });
});
