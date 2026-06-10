import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { LimitedModeBanner } from "@/components/features/auth/limited-mode-banner";
import { MfaBanner } from "@/components/features/auth/mfa-banner";
import { fetchCurrentUser } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { assertAllowedRole, sanitizeNextParam } from "@/lib/auth/route-guards";

/**
 * Authenticated route group layout — wraps every page under `/(authenticated)/*`.
 *
 * **Three layered guards (Story 1.7 §AC8 / code-review D5):**
 *
 * 1. **Auth guard** — `fetchCurrentUser()` throws on 401/403. The catch
 *    redirects to `/auth/login?next=<sanitized-original-path>` so the
 *    user lands back on the requested page after re-auth.
 * 2. **Role guard** — `assertAllowedRole(pathname, role)` compares the
 *    user's role against `ROUTE_ALLOWED_ROLES`. Refused users redirect
 *    to `/auth/forbidden?from=<sanitized-path>` (a dead-end page).
 * 3. **UX banners** — `MfaBanner` for staff non-enrolled (Story 1.6
 *    §AC8), `LimitedModeBanner` for pending-parental-consent kids
 *    (Story 1.4 §AC7). Both self-hide when not applicable.
 *
 * Pathname is read from the `x-pathname` header injected by the root
 * `middleware.ts` (Next.js 15 does not expose pathname to Server
 * Components natively).
 */
export default async function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const hdrs = await headers();
  const pathname = hdrs.get("x-pathname") ?? "/";
  const safeNext = sanitizeNextParam(pathname);

  // 1. Auth guard
  let role: string | null = null;
  try {
    const user = await fetchCurrentUser();
    role = user.role;
  } catch (cause) {
    if (cause instanceof ApiError && (cause.status === 401 || cause.status === 403)) {
      redirect(`/auth/login?next=${encodeURIComponent(safeNext)}`);
    }
    // Other errors bubble up to the global error boundary.
    throw cause;
  }

  // 2. Role guard
  const verdict = assertAllowedRole(pathname, role as Parameters<typeof assertAllowedRole>[1]);
  if (verdict === "redirect-login") {
    redirect(`/auth/login?next=${encodeURIComponent(safeNext)}`);
  }
  if (verdict === "forbidden") {
    redirect(`/auth/forbidden?from=${encodeURIComponent(safeNext)}`);
  }

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <MfaBanner />
      <LimitedModeBanner />
      {children}
    </div>
  );
}
