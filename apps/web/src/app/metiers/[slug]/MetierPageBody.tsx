"use client";

import { useSyncExternalStore } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import type { Profession } from "@/components/professions/types";
import type { SignalContributif } from "@/lib/api/recommendations";

import { FicheMetierClient } from "./FicheMetierClient";

/**
 * Client body of `/metiers/{slug}` — everything that depends on the
 * `?score=&confidence=&signals=` query params.
 *
 * Epic 7 review fix: the page previously `await`ed `searchParams` in the
 * Server Component, which forces dynamic rendering on EVERY request and
 * silently disabled its `revalidate = 3600` ISR (AC2 of Story 7.1). The
 * query params only ever personalize the view for a student arriving from
 * their authenticated recommendations list — pure client-side concern.
 *
 * Story 7.9 fix: that first fix read the params via `useSearchParams()`,
 * which forces a Suspense fallback on static/ISR prerender — and the
 * fallback was `null`, so the prerendered HTML was an EMPTY SHELL and the
 * LCP element only painted after hydration (render delay ≈ 2,3 s). The
 * params are now read from `window.location.search` through
 * `useSyncExternalStore` (server snapshot: empty string — same pattern as
 * `useMediaQuery` in `FicheMetier`). Consequences, all deliberate:
 *
 * - The prerendered/cached HTML is the full ANONYMOUS fiche (title,
 *   description, sections, signup CTA) — LCP paints from the initial HTML,
 *   and a student's personal score can never be frozen into the cached
 *   HTML / SERP snippet.
 * - Hydration renders with the server snapshot (`""`), so it matches the
 *   server HTML exactly — no hydration mismatch. React then re-checks the
 *   client snapshot on mount and re-renders once with the real query
 *   string, upgrading the view to the personalized variant (score badge,
 *   drawer, CTA hidden) for students arriving from `/mes-metiers`. Only
 *   those students see that one-frame anonymous→personalized swap;
 *   anonymous visitors (SEO, the Lighthouse gate) render once.
 * - The store never notifies (`subscribe` is a no-op): the query string
 *   only changes with a navigation, which normally remounts this page.
 *   `popstate` is still subscribed for the one case that does NOT remount:
 *   browser back/forward between two query-string variants of the SAME
 *   URL (e.g. `?score=82` → `?score=impossible`). Nothing on this page
 *   mutates the query string itself, so `pushState` (which does not emit
 *   `popstate`) is not a concern here.
 */

function subscribeToLocationSearch(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

function useLocationSearch(): string {
  return useSyncExternalStore(
    subscribeToLocationSearch,
    () => window.location.search,
    () => "",
  );
}

function parseSignals(raw: string | null): SignalContributif[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(decodeURIComponent(raw));
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (s) =>
        typeof s === "object" &&
        s !== null &&
        typeof s.signal === "string" &&
        typeof s.contribution === "number" &&
        typeof s.weight === "number",
    );
  } catch {
    return [];
  }
}

export function MetierPageBody({ profession }: { profession: Profession }) {
  const t = useTranslations("metierPage");
  const searchParams = new URLSearchParams(useLocationSearch());

  const scoreStr = searchParams.get("score");
  const confidence = searchParams.get("confidence");
  const rawSignals = searchParams.get("signals");

  const score = scoreStr !== null ? parseInt(scoreStr, 10) : undefined;
  const VALID_CONFIDENCE = new Set(["low", "medium", "high"]);
  const rawConfidence =
    confidence && VALID_CONFIDENCE.has(confidence)
      ? (confidence as "low" | "medium" | "high")
      : undefined;
  const confidenceLevel: "normal" | "indicative" | undefined =
    rawConfidence === "low" ? "indicative" : rawConfidence ? "normal" : undefined;

  const signalsContributifs = parseSignals(rawSignals);
  const arrivedFromAuthenticatedFlow = score !== undefined && Number.isFinite(score);

  return (
    <>
      {arrivedFromAuthenticatedFlow ? (
        <Link
          href="/mes-metiers"
          className="hover:text-text-primary mb-4 flex items-center gap-1 text-body-sm text-text-muted"
        >
          {t("myMetiersLink")}
        </Link>
      ) : (
        <Link
          href="/metiers"
          className="hover:text-text-primary mb-4 flex items-center gap-1 text-body-sm text-text-muted"
        >
          {t("backToList")}
        </Link>
      )}

      <FicheMetierClient
        profession={profession}
        score={arrivedFromAuthenticatedFlow ? score : undefined}
        confidenceLevel={confidenceLevel}
        drawerConfidenceLevel={rawConfidence}
        signalsContributifs={signalsContributifs}
      />

      {!arrivedFromAuthenticatedFlow && (
        <section
          aria-labelledby="signup-cta-title"
          className="mt-8 rounded-lg border border-border bg-card p-6 text-center"
        >
          <h2 id="signup-cta-title" className="mb-2 text-h3 font-semibold text-text">
            {t("signupCtaTitle")}
          </h2>
          <p className="mb-4 text-body-sm text-text-muted">
            {t("signupCtaBody", { name: profession.name })}
          </p>
          <Link
            href="/auth/signup"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-body-sm font-medium text-primary-foreground hover:opacity-90"
          >
            {t("signupCta")}
          </Link>
        </section>
      )}
    </>
  );
}
