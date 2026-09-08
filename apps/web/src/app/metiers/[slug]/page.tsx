import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchPublicProfession } from "@/lib/api/professions";
import { serializeJsonLd } from "@/lib/seo/json-ld";
import { SITE_ORIGIN, buildOccupationJsonLd } from "@/lib/seo/occupation-landing";

import { MetierPageBody } from "./MetierPageBody";

/**
 * `/metiers/{slug}` — Story 7.1 (SSR fiche métier indexable, AC1).
 *
 * Public route (no `(authenticated)` layout, no auth check) — the same
 * URL serves both an anonymous visitor (SEO/direct link — CTA to sign up)
 * and a logged-in student arriving from their recommendations list with
 * `?score=&confidence=&signals=` query params. Those params are read
 * client-side in `MetierPageBody` from `window.location.search` — never
 * `await searchParams` here (forces dynamic rendering, makes `revalidate`
 * inert) and never `useSearchParams` there (forces a Suspense fallback on
 * prerender, i.e. an empty LCP shell — Story 7.9). See `MetierPageBody`'s
 * docstring for the full history.
 *
 * `revalidate = 3600` — AC2: CDN-cacheable HTML, 1h TTL (on-demand
 * revalidation on a moderation/report signal is Story 3.8's existing
 * `ProfessionReport` flow, out of scope here).
 */
export const revalidate = 3600;

// Epic 7 review fix: without `generateStaticParams` a dynamic segment is
// server-rendered on every request even with `revalidate` set. Returning
// `[]` (rather than fetching all slugs) keeps the Docker image build free
// of a live-API dependency — every slug is ISR-rendered on first request,
// then cached for the `revalidate` TTL.
export function generateStaticParams(): { slug: string }[] {
  return [];
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const profession = await fetchPublicProfession(slug);
    const title = `${profession.name} — Path Advisor`;
    // Story 7.6 fix (same class of bug as `/formations/[slug]`): an empty
    // `description` would otherwise produce no `<meta name="description">`
    // tag at all — defensive fallback even though no currently-seeded
    // profession has an empty description.
    const t = await getTranslations("metierPage");
    const description = profession.description
      ? profession.description.slice(0, 155)
      : t("descriptionFallback", { name: profession.name });
    // Story 7.5 AC — og:image comes from the sibling `opengraph-image.tsx`
    // (Next.js file convention); Twitter falls back to it (see root
    // `page.tsx` for the rationale).
    return {
      title,
      description,
      // Epic 7 review fix — canonical strips the `?score=&confidence=&
      // signals=` personalization params, which otherwise make this page
      // crawlable as unlimited duplicate URLs. Relative path, resolved
      // against the root layout's `metadataBase`.
      alternates: { canonical: `/metiers/${slug}` },
      openGraph: {
        title,
        description,
        url: `${SITE_ORIGIN}/metiers/${slug}`,
        type: "website",
      },
      twitter: { card: "summary_large_image", title, description },
    };
  } catch {
    const t = await getTranslations("metierPage");
    return { title: t("metaTitleFallback") };
  }
}

export default async function MetierDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

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

  // Story 7.4 AC — Occupation JSON-LD on the canonical fiche métier
  // (Google Rich Results Test target for "une fiche métier").
  const occupationJsonLd = buildOccupationJsonLd(profession, `${SITE_ORIGIN}/metiers/${slug}`);

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: serializeJsonLd(occupationJsonLd) }}
      />
      {/* Story 7.9 — no Suspense boundary here on purpose. MetierPageBody
          is a Client Component but reads the personalization query params
          from `window.location.search` (post-hydration), NOT from
          `useSearchParams()`, so it prerenders as full anonymous HTML
          (LCP in the initial response) while keeping ISR effective. The
          previous `<Suspense fallback={null}>` + `useSearchParams` combo
          prerendered an EMPTY SHELL — see MetierPageBody's docstring. */}
      <MetierPageBody profession={profession} />
    </main>
  );
}
