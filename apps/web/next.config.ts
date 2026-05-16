import type { NextConfig } from "next";

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

export default nextConfig;
