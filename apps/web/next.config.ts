import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

/**
 * Next.js configuration.
 *
 * **Build flag note (`package.json` → `build: "next build --webpack"`):**
 * Next 16.2.x ships a Turbopack-as-default build that currently fails to
 * resolve `@vercel/turbopack-next/internal/font/google/font` when
 * `next/font/google` is used (Story 1.1 wires Inter via that loader in
 * `src/app/layout.tsx`). Until Vercel ships the fix, `next build --webpack`
 * pins the build to the legacy webpack pipeline. `next dev` keeps using
 * Turbopack for fast HMR.
 *
 * Revisit this when Next 16 publishes a patch and remove the `--webpack` flag
 * once `next build` succeeds without it.
 */
const nextConfig: NextConfig = {
  /* config options here */
};

// Story 7.7 — points at `src/i18n/request.ts` (the default next-intl looks
// for), which resolves the request-scoped `messages/fr.json`. No `[locale]`
// route segment/middleware — single-locale MVP (see `src/i18n/config.ts`).
const withNextIntl = createNextIntlPlugin();

export default withNextIntl(nextConfig);
