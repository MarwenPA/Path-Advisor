"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

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
 * their authenticated recommendations list — pure client-side concern — so
 * they're now read here via `useSearchParams()` (inside a `<Suspense>`
 * boundary in the page) and the server-rendered/cached HTML stays the
 * anonymous variant Google sees. Bonus: a student's personal score can no
 * longer be frozen into the cached HTML / SERP snippet.
 */

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
  const searchParams = useSearchParams();

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
