/**
 * Role-based post-login redirect — Story 1.5 §AC8.
 *
 * Every authenticated user lands on the route picked by their `role`. Student
 * and parent dashboards shipped with Epic 3 (`/mes-metiers`) and Epic 6
 * (`/parent`) respectively — updated here per Story 7.8 code review (the
 * homepage's "redirect an authenticated visitor" guard reuses this same
 * table, which surfaced the fact it had gone stale since those epics shipped).
 * Roles without a dashboard yet (counselor, school_admin, support — Epic 6/9
 * backlog) still fall back to `/parametres/confidentialite`. Future stories
 * shipping those dashboards touch this single file.
 *
 * Important: the redirect is UX only. Every authenticated route MUST
 * independently check `request.user.role` server-side (Story 1.7 RBAC) — a
 * forged redirect target gives no privilege escalation.
 */

import type { UserRole, UserStatus } from "@/lib/api/auth";

/**
 * Fallback for roles without a dedicated dashboard yet (counselor,
 * school_admin, support — Epic 6/9 backlog). Every signed-in user without a
 * role-specific destination lands on the privacy/data settings page — the
 * only generic authenticated route guaranteed to exist for every role
 * (`ROUTE_ALLOWED_ROLES["/parametres"]` in `route-guards.ts` allows all).
 */
export const MVP_FALLBACK_PATH = "/parametres/confidentialite";

const ROLE_TO_PATH: Record<UserRole, string> = {
  // Story 8.8 — modular home (recommendations + progress + mes-paris), the
  // student's real home. `/mes-metiers` (Epic 3) is not removed — the
  // "Voir tous mes métiers" module link still points to it.
  student: "/accueil",
  // Epic 6 (Story 6.2) — parent dashboard (métiers explorés / mes paris / coûts).
  parent: "/parent",
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
