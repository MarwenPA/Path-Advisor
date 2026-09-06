import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchPublicProfession } from "@/lib/api/professions";
import type { SignalContributif } from "@/lib/api/recommendations";
import { SITE_ORIGIN, buildOccupationJsonLd } from "@/lib/seo/occupation-landing";

import { FicheMetierClient } from "./FicheMetierClient";

/**
 * `/metiers/{slug}` — Story 7.1 (SSR fiche métier indexable, AC1).
 *
 * Public route (no `(authenticated)` layout, no auth check) — the same
 * URL serves both an anonymous visitor (SEO/direct link — CTA to sign up)
 * and a logged-in student arriving from their recommendations list with
 * `?score=&confidence=&signals=` query params (unchanged since before this
 * story; `fetchPublicProfession` is the `AllowAny` backend endpoint, so no
 * auth cookie is required either way). `signals`/`score` in the query
 * string is how we distinguish "arrived from an authenticated flow" from
 * "generic public visit" — good enough without a separate session check.
 *
 * `revalidate = 3600` — AC2: CDN-cacheable HTML, 1h TTL (on-demand
 * revalidation on a moderation/report signal is Story 3.8's existing
 * `ProfessionReport` flow, out of scope here).
 */
export const revalidate = 3600;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const profession = await fetchPublicProfession(slug);
    return {
      title: `${profession.name} — Path Advisor`,
      description: profession.description.slice(0, 155),
    };
  } catch {
    return { title: "Fiche métier — Path Advisor" };
  }
}

function parseSignals(raw: string | undefined): SignalContributif[] {
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

export default async function MetierDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ score?: string; confidence?: string; signals?: string }>;
}) {
  const { slug } = await params;
  const { score: scoreStr, confidence, signals: rawSignals } = await searchParams;

  let profession;
  try {
    profession = await fetchPublicProfession(slug);
  } catch (err) {
    // Code-review fix (Story 7.1) — missing `return` after `notFound()`
    // meant a 404 always fell through to `throw err` too (same bug class
    // fixed repeatedly earlier this session, e.g. Story 6.3).
    if (err instanceof ApiError && err.status === 404) {
      notFound();
      return null;
    }
    throw err;
  }

  const score = scoreStr !== undefined ? parseInt(scoreStr, 10) : undefined;
  const VALID_CONFIDENCE = new Set(["low", "medium", "high"]);
  const rawConfidence =
    confidence && VALID_CONFIDENCE.has(confidence)
      ? (confidence as "low" | "medium" | "high")
      : undefined;
  const confidenceLevel: "normal" | "indicative" | undefined =
    rawConfidence === "low" ? "indicative" : rawConfidence ? "normal" : undefined;

  const signalsContributifs = parseSignals(rawSignals);
  const arrivedFromAuthenticatedFlow = score !== undefined && Number.isFinite(score);
  // Story 7.4 AC — Occupation JSON-LD on the canonical fiche métier
  // (Google Rich Results Test target for "une fiche métier").
  const occupationJsonLd = buildOccupationJsonLd(profession, `${SITE_ORIGIN}/metiers/${slug}`);

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(occupationJsonLd) }}
      />
      {arrivedFromAuthenticatedFlow ? (
        <Link
          href="/mes-metiers"
          className="hover:text-text-primary mb-4 flex items-center gap-1 text-body-sm text-text-muted"
        >
          ← Mes métiers
        </Link>
      ) : (
        <Link
          href="/metiers"
          className="hover:text-text-primary mb-4 flex items-center gap-1 text-body-sm text-text-muted"
        >
          ← Tous les métiers
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
            Découvre tes vraies chances
          </h2>
          <p className="mb-4 text-body-sm text-text-muted">
            Crée ton compte gratuit pour voir ton score de compatibilité personnalisé avec{" "}
            {profession.name} et tes probabilités d&apos;admission réelles.
          </p>
          <Link
            href="/auth/signup"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-body-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Crée ton compte pour voir tes chances réelles
          </Link>
        </section>
      )}
    </main>
  );
}
