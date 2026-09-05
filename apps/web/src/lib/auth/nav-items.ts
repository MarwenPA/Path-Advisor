/**
 * Navigation registry — Story 1.15 (UX-DR31).
 *
 * `NAV_ITEMS` is deliberately a SEPARATE registry from `ROUTE_ALLOWED_ROLES`
 * (`./route-guards.ts`), never derived from it. `ROUTE_ALLOWED_ROLES` answers
 * "who is ALLOWED to see this route" (server-side guard, includes routes
 * declared ahead of their page shipping — e.g. `/cohorte`, `/ecole`,
 * `/support`). `NAV_ITEMS` answers "which route is far enough along to be
 * SHOWN in the nav" — a strictly narrower set. If a future change made
 * `NAV_ITEMS` a filter over `ROUTE_ALLOWED_ROLES`, the nav would immediately
 * grow dead links to any route declared-but-not-shipped, defeating the whole
 * point of this story. See the "Navigation Multi-Rôle" addendum in
 * `_bmad-output/planning-artifacts/ux-design-specification.md` for the full
 * design rationale (Revolut/N26: items reflect what THIS account can do).
 *
 * Every new page that ships adds its own entry here — never the reverse.
 */

import { Briefcase, GraduationCap, Home, Sparkles, User, type LucideIcon } from "lucide-react";

import type { UserRole } from "@/lib/api/auth";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** True for links that leave the Next app entirely (e.g. Django admin). */
  external?: boolean;
}

export const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  student: [
    { href: "/accueil", label: "Accueil", icon: Home },
    { href: "/mes-metiers", label: "Mes métiers", icon: Briefcase },
    { href: "/mes-paris", label: "Mes paris", icon: GraduationCap },
    { href: "/premium", label: "Premium", icon: Sparkles },
    // Story 1.15 follow-up (2026-09) — `/profile` just moved under
    // `(authenticated)/`; this is the 5th and last item the "5 onglets max"
    // rule (UX design doc, Navigation Patterns) allows on the mobile tab bar.
    { href: "/profile", label: "Mon profil", icon: User },
  ],
  parent: [{ href: "/parent", label: "Tableau de bord", icon: Home }],
  // `/cohorte` is already declared in `ROUTE_ALLOWED_ROLES` (guard-ready) but
  // has no page yet (Epic 6 backlog) — no nav item until it ships.
  counselor: [],
  // Same reasoning — `/ecole` (Epic 6/9 backlog).
  school_admin: [],
  // Same reasoning — `/support` (Epic 9 backlog).
  support: [],
  // `path_admin` uses Django admin (separate session cookie) — external link,
  // never a Next route. See `post-login-redirect.ts` for the same pattern.
  path_admin: [{ href: "/admin/", label: "Admin", icon: Home, external: true }],
};

/**
 * Bottom tab bar only makes sense with ≥ 2 metier items — a single item next
 * to the account icon looks broken (2 icons total). Below that threshold,
 * `MobileNav` renders a sticky header + account icon instead.
 */
export function hasBottomTabBar(role: UserRole): boolean {
  return NAV_ITEMS[role].length >= 2;
}
