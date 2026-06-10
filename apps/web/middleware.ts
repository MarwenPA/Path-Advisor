import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Edge middleware — Story 1.7 §AC8.
 *
 * Sets `x-pathname` on outgoing request headers so Server Components in the
 * `(authenticated)/layout.tsx` route group can read the current pathname.
 * Next.js 15 does NOT expose the pathname to Server Components by default;
 * the canonical workaround is this single-line middleware.
 *
 * Matcher excludes static assets + Next.js internals to keep the runtime
 * overhead negligible.
 */
export function middleware(request: NextRequest) {
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
