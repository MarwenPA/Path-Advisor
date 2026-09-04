import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Edge proxy — Story 1.7 §AC8.
 *
 * Sets `x-pathname` on outgoing request headers so Server Components in the
 * `(authenticated)/layout.tsx` route group can read the current pathname.
 * Next.js does NOT expose the pathname to Server Components by default;
 * the canonical workaround is this single-line proxy.
 *
 * Bug fix (2026-09): this file used to be `middleware.ts` exporting
 * `middleware()` — the Next.js 16 convention (this repo is on 16.2.x, see
 * `AGENTS.md`). `middleware.ts` was renamed to `proxy.ts` / `proxy()` in
 * v16.0.0; the old file was no longer picked up at all, so `x-pathname` was
 * never set and `AuthenticatedLayout` silently fell back to its `?? "/"`
 * default for every authenticated page — which matches no prefix in
 * `ROUTE_ALLOWED_ROLES`, so EVERY authenticated route (login included)
 * 403'd via the fail-closed default. See `node_modules/next/dist/docs/
 * 01-app/03-api-reference/03-file-conventions/proxy.md` § Migration to Proxy.
 *
 * Location matters too: the docs say "create `proxy.ts` in the project
 * root, **or inside `src` if applicable**, at the same level as `pages` or
 * `app`" — this repo's App Router lives at `src/app/`, so the file MUST be
 * `src/proxy.ts`. A `proxy.ts` sitting at the package root (next to `src/`)
 * is silently never invoked, confirmed by instrumenting it and seeing zero
 * log lines until it was moved here.
 *
 * Matcher excludes static assets + Next.js internals to keep the runtime
 * overhead negligible.
 */
export function proxy(request: NextRequest) {
  const headers = new Headers(request.headers);
  headers.set("x-pathname", request.nextUrl.pathname);
  return NextResponse.next({ request: { headers } });
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static / _next/image (Next.js build assets)
     * - favicon.ico / robots.txt / sitemap.xml (static at root)
     * - public/* (project static)
     */
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|public/).*)",
  ],
};
