import type { MetadataRoute } from "next";

import { PRODUCTION_ORIGIN, SITE_ORIGIN } from "@/lib/seo/occupation-landing";

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
 *
 * Epic 7 review fixes:
 * - prefixes are slash-less: `Disallow: /parametres/` does NOT match
 *   `/parametres` (the URL actually served — Next.js strips trailing
 *   slashes), so the whole authenticated area was crawlable. A slash-less
 *   prefix matches both forms. None of the public routes (`/metiers`,
 *   `/formations`, `/devenir-*`, niveau pages, `/legal`) share any of
 *   these prefixes, so no over-blocking.
 * - a non-production deploy (SITE_ORIGIN overridden via
 *   `NEXT_PUBLIC_SITE_ORIGIN`) disallows EVERYTHING and advertises no
 *   sitemap — staging must never be indexed nor point crawlers at
 *   production URLs.
 */
export default function robots(): MetadataRoute.Robots {
  if (SITE_ORIGIN !== PRODUCTION_ORIGIN) {
    return {
      rules: { userAgent: "*", disallow: "/" },
    };
  }

  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/api",
        "/admin",
        "/parametres",
        "/onboarding",
        "/accueil",
        "/mes-metiers",
        "/mes-paris",
        "/mes-envois",
        "/profile",
        "/premium",
        "/parent",
        "/support",
        "/cohorte",
        "/ecole",
        "/auth",
        "/schools",
      ],
    },
    sitemap: `${SITE_ORIGIN}/sitemap.xml`,
  };
}
