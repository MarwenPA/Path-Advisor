/**
 * Role-based post-login redirect — Story 1.5 §AC8.
 *
 * Every authenticated user lands on the route picked by their `role`. For MVP
 * most role-specific dashboards (parent, counselor, school) are not yet
 * shipped — they all redirect to `/parametres/confidentialite`, the only
 * authenticated route that actually exists today. Future stories editing the
 * redirect table touch this single file.
 *
 * Important: the redirect is UX only. Every authenticated route MUST
 * independently check `request.user.role` server-side (Story 1.7 RBAC) — a
 * forged redirect target gives no privilege escalation.
 */

import type { UserRole, UserStatus } from "@/lib/api/auth";

/**
 * MVP fallback: most role-specific dashboards don't exist yet (Epics 2-6).
 * Until they ship, every signed-in user lands on the privacy/data settings
 * page — the only authenticated route guaranteed to exist.
 */
export const MVP_FALLBACK_PATH = "/parametres/confidentialite";

const ROLE_TO_PATH: Record<UserRole, string> = {
  // Students → MVP fallback until Epic 2 onboarding + Epic 3 recommendations
  // ship. When 2.1/2.2 land, route to `/onboarding` for incomplete profiles
  // and `/recommendations` otherwise.
  student: MVP_FALLBACK_PATH,
  parent: MVP_FALLBACK_PATH, // Epic 6 — parent space placeholder.
  counselor: MVP_FALLBACK_PATH, // Epic 6 — B2B counselor dashboard placeholder.
  school_admin: MVP_FALLBACK_PATH, // Epics 5/6 — school space placeholder.
  // path_admin uses Django admin (separate cookie auth there) — frontend
  // opens it in a new tab rather than nav'ing the SPA.
  path_admin: "/admin/",
  support: MVP_FALLBACK_PATH, // Story 1.7 — support role; future support dashboard.
};

export function getPostLoginPath(role: UserRole, _status: UserStatus): string {
  // `_status` is reserved for the future "incomplete profile → /onboarding"
  // gate (Epic 2). Kept in the signature so consumers don't have to refactor
  // their call sites when the gate lands.
  return ROLE_TO_PATH[role] ?? MVP_FALLBACK_PATH;
}
