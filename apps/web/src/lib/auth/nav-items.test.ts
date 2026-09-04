/**
 * `NAV_ITEMS` / `hasBottomTabBar` unit tests — Story 1.15.
 */
import { describe, expect, it } from "vitest";

import { NAV_ITEMS, hasBottomTabBar } from "./nav-items";
import { ROUTE_ALLOWED_ROLES } from "./route-guards";

const ALL_ROLES = [
  "student",
  "parent",
  "counselor",
  "school_admin",
  "path_admin",
  "support",
] as const;

describe("NAV_ITEMS", () => {
  it("has an entry for every UserRole", () => {
    for (const role of ALL_ROLES) {
      expect(NAV_ITEMS[role]).toBeDefined();
    }
  });

  it("never links to a route the role isn't allowed to see (per ROUTE_ALLOWED_ROLES)", () => {
    // Regression guard for the story's central rule: NAV_ITEMS must be a
    // NARROWER set than ROUTE_ALLOWED_ROLES, never wider — every internal
    // (non-external) nav link's longest matching ROUTE_ALLOWED_ROLES prefix
    // must include the role it's shown to.
    const prefixes = Object.keys(ROUTE_ALLOWED_ROLES).sort((a, b) => b.length - a.length);

    for (const role of ALL_ROLES) {
      for (const item of NAV_ITEMS[role]) {
        if (item.external) continue;
        const prefix = prefixes.find((p) => item.href === p || item.href.startsWith(`${p}/`));
        expect(prefix, `${item.href} has no ROUTE_ALLOWED_ROLES entry`).toBeDefined();
        expect(ROUTE_ALLOWED_ROLES[prefix as string]).toContain(role);
      }
    }
  });

  it("counselor, school_admin and support have no shipped nav items yet", () => {
    expect(NAV_ITEMS.counselor).toEqual([]);
    expect(NAV_ITEMS.school_admin).toEqual([]);
    expect(NAV_ITEMS.support).toEqual([]);
  });

  it("path_admin's only item is external (Django admin)", () => {
    expect(NAV_ITEMS.path_admin).toHaveLength(1);
    expect(NAV_ITEMS.path_admin[0]?.external).toBe(true);
  });
});

describe("hasBottomTabBar", () => {
  it("is true only for roles with >= 2 nav items", () => {
    expect(hasBottomTabBar("student")).toBe(true);
    expect(hasBottomTabBar("parent")).toBe(false);
    expect(hasBottomTabBar("counselor")).toBe(false);
    expect(hasBottomTabBar("school_admin")).toBe(false);
    expect(hasBottomTabBar("support")).toBe(false);
    expect(hasBottomTabBar("path_admin")).toBe(false);
  });
});
