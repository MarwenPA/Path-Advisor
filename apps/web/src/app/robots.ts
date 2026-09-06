import type { MetadataRoute } from "next";

import { SITE_ORIGIN } from "@/lib/seo/occupation-landing";

/**
 * `/robots.txt` — Story 7.4 AC. Next.js file convention (`app/robots.ts`)
 * auto-serves this at the site root; `src/proxy.ts`'s matcher already
 * excludes `robots.txt` from the `x-pathname` header injection so this
 * route is never touched by the `(authenticated)` layout guard.
 *
 * Disallows every route-guard-protected prefix from
 * `lib/auth/route-guards.ts` (`ROUTE_ALLOWED_ROLES`) plus `/api/` and
 * `/admin/` (Django admin, not the Next.js `/admin` app area, but
 * disallowed all the same defensively) — kept as a literal list rather
 * than importing the route-guards module (that file has zero business
 * being bundled into a crawler-facing static file).
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/api/",
        "/admin/",
        "/parametres/",
        "/onboarding/",
        "/accueil/",
        "/mes-metiers/",
        "/mes-paris/",
        "/mes-envois/",
        "/profile/",
        "/premium/",
        "/parent/",
        "/support/",
        "/cohorte/",
        "/ecole/",
        "/auth/",
        "/schools/",
      ],
    },
    sitemap: `${SITE_ORIGIN}/sitemap.xml`,
  };
}
