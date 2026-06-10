/**
 * Frontend RBAC route guards — Story 1.7 §AC8.
 *
 * `assertAllowedRole(path, role)` returns:
 *   - "allow"           → the user can render the page.
 *   - "forbidden"       → the user is authenticated but lacks the role.
 *   - "redirect-login"  → the caller should send the user to /auth/login.
 *
 * The mapping is path-prefix based — `/parametres/*` allows any role,
 * `/admin/*` allows only `path_admin` + `support`, etc. New protected
 * route trees declare their allow-list in `ROUTE_ALLOWED_ROLES` below.
 *
 * **Caller pattern (in `(authenticated)/layout.tsx`):**
 *   const user = await fetchCurrentUser();
 *   const verdict = assertAllowedRole(headers().get("x-pathname") ?? "/", user.role);
 *   if (verdict === "redirect-login") redirect(`/auth/login?next=${path}`);
 *   if (verdict === "forbidden") redirect(`/auth/forbidden?from=${path}`);
 */

import type { UserRole } from "@/lib/api/auth";

/**
 * Path prefix → allowed roles. Prefixes are matched longest-first so a
 * narrower rule (e.g. `/parametres/admin/`) wins over a broader one
 * (`/parametres/`).
 */
export const ROUTE_ALLOWED_ROLES: Record<string, ReadonlyArray<UserRole>> = {
  // Generic authenticated areas — any role
  "/parametres": ["student", "parent", "counselor", "school_admin", "path_admin", "support"],
  "/onboarding": ["student"],
  // Future staff areas (declared early so the matrix is exhaustive)
  "/admin": ["path_admin"],
  "/support": ["support", "path_admin"],
  "/cohorte": ["counselor", "path_admin"],
  "/ecole": ["school_admin", "path_admin"],
};

export type RouteGuardVerdict = "allow" | "forbidden" | "redirect-login";

/**
 * Resolve a verdict for the given path + user role.
 *
 * `role === null` indicates anonymous → "redirect-login".
 * No matching prefix → "allow" (caller should not call us for unprotected
 * paths; this is a defensive default to avoid accidental lockouts on a
 * route the matrix forgot).
 */
export function assertAllowedRole(path: string, role: UserRole | null): RouteGuardVerdict {
  if (role === null) {
    return "redirect-login";
  }

  // Find the longest prefix that matches.
  const prefixes = Object.keys(ROUTE_ALLOWED_ROLES).sort((a, b) => b.length - a.length);
  for (const prefix of prefixes) {
    if (path === prefix || path.startsWith(prefix + "/")) {
      const allowed = ROUTE_ALLOWED_ROLES[prefix] ?? [];
      return allowed.includes(role) ? "allow" : "forbidden";
    }
  }

  // Code-review P12 — fail CLOSED for unknown paths under the
  // `(authenticated)` route group. A new staff page added without an
  // entry in `ROUTE_ALLOWED_ROLES` would otherwise be rendered to every
  // role. The forbidden page guides the dev to update the matrix.
  return "forbidden";
}

/**
 * Sanitize a `next` query param to prevent open-redirect (NIST SP 800-63B).
 * Returns the path if it's a local URL, else `/` as fallback.
 */
export function sanitizeNextParam(next: string | null): string {
  if (!next) return "/";
  // Code-review P13 — refuse any whitespace (CR/LF/tab/space). Older browsers
  // trim leading whitespace from URL attributes and may then misinterpret
  // a payload like `/\t//attacker.test/` as protocol-relative. Whitespace
  // is also a CRLF-injection vector if `next` ever lands in a header.
  if (/\s/.test(next)) return "/";
  // Refuse anything starting with `//`, `\\`, or containing a scheme.
  if (next.startsWith("//") || next.startsWith("\\") || /^[a-z][a-z0-9+.-]*:/i.test(next)) {
    return "/";
  }
  // Must start with `/` (local path)
  if (!next.startsWith("/")) return "/";
  return next;
}
