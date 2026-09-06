/**
 * `/robots.txt` tests — Story 7.4.
 */
import { describe, expect, it } from "vitest";

import robots from "./robots";

describe("robots", () => {
  it("allows public pages and points to the sitemap", () => {
    const result = robots();
    expect(result.rules).toMatchObject({ userAgent: "*", allow: "/" });
    expect(result.sitemap).toBe("https://path-advisor.fr/sitemap.xml");
  });

  it("disallows every application/admin route prefix", () => {
    const result = robots();
    const disallow = (result.rules as { disallow: string[] }).disallow;
    expect(disallow).toEqual(
      expect.arrayContaining(["/api/", "/admin/", "/parametres/", "/auth/", "/schools/"]),
    );
  });

  it("does not disallow the public SEO routes", () => {
    const result = robots();
    const disallow = (result.rules as { disallow: string[] }).disallow;
    expect(disallow).not.toContain("/metiers/");
    expect(disallow).not.toContain("/formations/");
  });
});
