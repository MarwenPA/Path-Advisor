import Link from "next/link";
import { redirect, unstable_rethrow } from "next/navigation";

import { AhaMomentsSection } from "@/components/features/homepage/aha-moments-section";
import { HeroSection } from "@/components/features/homepage/hero-section";
import { HowItWorksSection } from "@/components/features/homepage/how-it-works-section";
import { TrustSection } from "@/components/features/homepage/trust-section";
import { fetchCurrentUser } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { getPostLoginPath } from "@/lib/auth/post-login-redirect";
import { SITE_ORIGIN } from "@/lib/seo/occupation-landing";

import type { Metadata } from "next";

const TITLE = "Path-Advisor — Trouve ta voie, étape par étape";
const DESCRIPTION =
  "Découvre les métiers qui te correspondent, comprends tes vraies chances d'admission et construis ton parcours d'orientation, du collège aux études supérieures.";

// Story 7.5 AC — og:title/description/image/url/type + Twitter Card.
// og:image comes from `app/opengraph-image.tsx` (Next.js file convention,
// auto-wired into this page's `<head>`); Twitter falls back to the same
// `og:image` per the Twitter Card spec when no dedicated `twitter:image`
// is set — no separate `twitter-image.tsx` needed.
export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: SITE_ORIGIN,
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
};

/**
 * Public landing page — Story 7.8.
 *
 * Replaces the Story 1.2 design-token demo seed. Redirects an already
 * authenticated visitor straight to their application space (§AC3), reusing
 * the same `getPostLoginPath` role→route table the login form uses (Story
 * 1.5 §AC8) — one source of truth for "where does this role land".
 * Any non-auth error (API hiccup, network blip, malformed payload) must NOT
 * break this page — it's the public front door and has to stay up even when
 * the API doesn't.
 */
export default async function Home() {
  try {
    const user = await fetchCurrentUser();
    redirect(getPostLoginPath(user.role, user.status));
  } catch (cause) {
    // `redirect()` throws Next's own control-flow error (digest-tagged) —
    // rethrow that untouched, no-op on anything else (code-review P1: an
    // earlier version here only recognized `ApiError` and rethrew
    // everything else, which crashed the public landing on a timeout,
    // network blip, or malformed `fetchCurrentUser()` payload).
    unstable_rethrow(cause);

    const isAnonymous = cause instanceof ApiError && (cause.status === 401 || cause.status === 403);
    if (!isAnonymous) {
      // 5xx, network failure, timeout, or a malformed user payload — log a
      // minimal summary (never the raw error object — code-review P4) and
      // fall through to the landing page render below.
      console.error("Home: fetchCurrentUser failed unexpectedly", {
        status: cause instanceof ApiError ? cause.status : undefined,
        message: cause instanceof Error ? cause.message : String(cause),
      });
    }
  }

  return (
    <main className="flex flex-1 flex-col">
      <HeroSection />
      <HowItWorksSection />
      <AhaMomentsSection />
      <TrustSection />
      <footer className="border-t border-border bg-bg px-4 py-8 text-center">
        <Link
          href="/legal/rgpd"
          className="text-caption text-text-subtle underline underline-offset-4 hover:text-text"
        >
          Mentions légales & RGPD
        </Link>
      </footer>
    </main>
  );
}
