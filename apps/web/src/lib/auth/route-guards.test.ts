/**
 * Route guards unit tests — Story 1.7 §AC8 / §T12.
 */
import { describe, expect, it } from "vitest";

import { assertAllowedRole, sanitizeNextParam } from "./route-guards";

describe("assertAllowedRole", () => {
  it("returns redirect-login for anonymous users", () => {
    expect(assertAllowedRole("/parametres/securite/mfa", null)).toBe("redirect-login");
    expect(assertAllowedRole("/admin/users", null)).toBe("redirect-login");
  });

  it("allows /parametres/* for every role", () => {
    for (const role of [
      "student",
      "parent",
      "counselor",
      "school_admin",
      "path_admin",
      "support",
    ] as const) {
      expect(assertAllowedRole("/parametres/securite/mfa", role)).toBe("allow");
    }
  });

  it("allows /onboarding/* only for student", () => {
    expect(assertAllowedRole("/onboarding/step1", "student")).toBe("allow");
    expect(assertAllowedRole("/onboarding/step1", "parent")).toBe("forbidden");
    expect(assertAllowedRole("/onboarding/step1", "counselor")).toBe("forbidden");
  });

  it("allows /accueil only for student (Story 8.8)", () => {
    expect(assertAllowedRole("/accueil", "student")).toBe("allow");
    for (const role of ["parent", "counselor", "school_admin", "path_admin", "support"] as const) {
      expect(assertAllowedRole("/accueil", role)).toBe("forbidden");
    }
  });

  it("allows /profile, /profile/history for student only (Story 1.15 follow-up)", () => {
    // /profile used to live in the (auth) route group with NO guard at all
    // until moved under (authenticated)/ — reachable from the nav now, so
    // it must also be role-gated like every other student page.
    for (const path of ["/profile", "/profile/history"]) {
      expect(assertAllowedRole(path, "student")).toBe("allow");
      for (const role of [
        "parent",
        "counselor",
        "school_admin",
        "path_admin",
        "support",
      ] as const) {
        expect(assertAllowedRole(path, role)).toBe("forbidden");
      }
    }
  });

  it("allows /mes-envois for student only (Story 5.4)", () => {
    expect(assertAllowedRole("/mes-envois", "student")).toBe("allow");
    for (const role of ["parent", "counselor", "school_admin", "path_admin", "support"] as const) {
      expect(assertAllowedRole("/mes-envois", role)).toBe("forbidden");
    }
  });

  it("allows /mes-metiers, /mes-paris for student only (code-review fix, Story 8.8)", () => {
    // These route trees existed since Epic 3/4 but had no matrix entry —
    // every authenticated user was silently redirected to /auth/forbidden.
    for (const path of ["/mes-metiers", "/mes-paris"]) {
      expect(assertAllowedRole(path, "student")).toBe("allow");
      for (const role of [
        "parent",
        "counselor",
        "school_admin",
        "path_admin",
        "support",
      ] as const) {
        expect(assertAllowedRole(path, role)).toBe("forbidden");
      }
    }
  });

  it("allows /metiers, /schools, /premium for student + parent (code-review fix, Story 8.8)", () => {
    for (const path of ["/metiers/some-slug", "/schools/some-slug", "/premium/success"]) {
      expect(assertAllowedRole(path, "student")).toBe("allow");
      expect(assertAllowedRole(path, "parent")).toBe("allow");
      expect(assertAllowedRole(path, "counselor")).toBe("forbidden");
    }
  });

  it("allows /admin/* only for path_admin", () => {
    expect(assertAllowedRole("/admin/users", "path_admin")).toBe("allow");
    expect(assertAllowedRole("/admin/users", "support")).toBe("forbidden");
    expect(assertAllowedRole("/admin/users", "student")).toBe("forbidden");
  });

  it("allows /cohorte/* only for counselor + path_admin", () => {
    expect(assertAllowedRole("/cohorte/dashboard", "counselor")).toBe("allow");
    expect(assertAllowedRole("/cohorte/dashboard", "path_admin")).toBe("allow");
    expect(assertAllowedRole("/cohorte/dashboard", "school_admin")).toBe("forbidden");
  });

  it("allows /ecole/* only for school_admin + path_admin", () => {
    expect(assertAllowedRole("/ecole/profils", "school_admin")).toBe("allow");
    expect(assertAllowedRole("/ecole/profils", "path_admin")).toBe("allow");
    expect(assertAllowedRole("/ecole/profils", "counselor")).toBe("forbidden");
  });

  it("fails CLOSED for unknown paths (code-review P12)", () => {
    // A new staff page added without a matrix entry must not leak to
    // unauthorized roles. Forcing the dev to update ROUTE_ALLOWED_ROLES
    // is the documented contract.
    expect(assertAllowedRole("/some-future-page", "student")).toBe("forbidden");
    expect(assertAllowedRole("/", "student")).toBe("forbidden");
  });

  it("matches longest prefix first", () => {
    // /parametres allows all; if a future /parametres/admin restricts to
    // path_admin only, the longer prefix wins. (Current matrix doesn't
    // have such a sub-rule but the algorithm must be order-correct.)
    expect(assertAllowedRole("/parametres/securite", "student")).toBe("allow");
  });
});

describe("sanitizeNextParam", () => {
  it("returns / for null / empty", () => {
    expect(sanitizeNextParam(null)).toBe("/");
    expect(sanitizeNextParam("")).toBe("/");
  });

  it("accepts local paths starting with /", () => {
    expect(sanitizeNextParam("/parametres/securite/mfa")).toBe("/parametres/securite/mfa");
    expect(sanitizeNextParam("/")).toBe("/");
  });

  it("rejects schemes (http, https, javascript, data, etc.)", () => {
    expect(sanitizeNextParam("https://attacker.test/")).toBe("/");
    expect(sanitizeNextParam("http://attacker.test/")).toBe("/");
    expect(sanitizeNextParam("javascript:alert(1)")).toBe("/");
    expect(sanitizeNextParam("data:text/html,...")).toBe("/");
  });

  it("rejects protocol-relative // and backslashes", () => {
    expect(sanitizeNextParam("//attacker.test/")).toBe("/");
    expect(sanitizeNextParam("\\\\attacker.test\\")).toBe("/");
  });

  it("rejects paths that don't start with /", () => {
    expect(sanitizeNextParam("parametres/securite")).toBe("/");
    expect(sanitizeNextParam("attacker.test")).toBe("/");
  });

  it("rejects any whitespace — CRLF / tab / leading-space (code-review P13)", () => {
    expect(sanitizeNextParam("/foo\r\nLocation: evil.com")).toBe("/");
    expect(sanitizeNextParam("/\tfoo")).toBe("/");
    expect(sanitizeNextParam(" /foo")).toBe("/");
    expect(sanitizeNextParam("/foo bar")).toBe("/");
  });
});
