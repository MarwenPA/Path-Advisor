import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchPublicProfession } from "@/lib/api/professions";
import { fetchPublicParcoursSummary } from "@/lib/api/schools";
import { serializeJsonLd } from "@/lib/seo/json-ld";
import {
  NIVEAU_SLUGS,
  SITE_ORIGIN,
  buildFaqPageJsonLd,
  buildOccupationFaq,
  buildOccupationJsonLd,
} from "@/lib/seo/occupation-landing";

/**
 * `/devenir-{metier}` — Story 7.3 AC1 (landing page long-tail SEO).
 *
 * Code-review fix during this story: Next.js App Router dynamic segments
 * MUST be the entire path segment (`[folderName]`) — there's no support
 * for a literal prefix glued to a bracket like `devenir-[metier]` (that
 * folder name is taken as a literal string, never matched as dynamic;
 * confirmed by a live 404 during the Docker smoke test). The fix: this
 * route lives at the top-level `[slug]` segment (shared with the sibling
 * `/{niveau}/quel-bac-pour-{metier}` route below it — Next.js requires
 * every dynamic folder at the same level to share one param name), and
 * the "devenir-" prefix is parsed out of `slug` here instead of by the
 * router. Anything not matching the prefix 404s — this path is reserved
 * for "devenir-*" URLs only.
 *
 * Reuses the Story 7.1/7.2 public endpoints — no new profession/school
 * data model, just a different combination + FAQ/Schema.org layer.
 */
export const revalidate = 3600;

// Epic 7 review fix — enables ISR; see `/metiers/[slug]/page.tsx` for why
// this returns `[]` instead of fetching all slugs at build time.
export function generateStaticParams(): { slug: string }[] {
  return [];
}

const DEVENIR_PREFIX = "devenir-";

function extractMetierSlug(slug: string): string | null {
  return slug.startsWith(DEVENIR_PREFIX) ? slug.slice(DEVENIR_PREFIX.length) : null;
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const metier = extractMetierSlug(slug);
  const t = await getTranslations("devenirMetierPage");
  if (!metier) return { title: t("metaTitleUnmatched") };
  try {
    const profession = await fetchPublicProfession(metier);
    const title = t("metaTitle", { name: profession.name });
    const description = t("metaDescription", {
      name: profession.name,
      excerpt: profession.description.slice(0, 100),
    });
    return {
      title,
      description,
      // Epic 7 review fix — explicit canonical (relative, resolved against
      // the root layout's `metadataBase`): this landing shares much of its
      // content with `/metiers/{slug}` and the niveau pages, so each URL
      // must declare itself unambiguously.
      alternates: { canonical: `/devenir-${metier}` },
      openGraph: {
        title,
        description,
        url: `${SITE_ORIGIN}/devenir-${metier}`,
        type: "website",
      },
      twitter: { card: "summary_large_image", title, description },
    };
  } catch {
    return { title: t("metaTitleFallback") };
  }
}

export default async function DevenirMetierPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const metier = extractMetierSlug(slug);
  if (!metier) {
    notFound();
    return null;
  }
  const t = await getTranslations("devenirMetierPage");
  // Niveau labels live under the sibling page's namespace (single source
  // of truth for the label of each niveau slug — Story 7.7 convention).
  const tNiveauLabels = await getTranslations("quelBacPourPage.niveauLabels");

  let profession;
  try {
    profession = await fetchPublicProfession(metier);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
      return null;
    }
    throw err;
  }

  const parcours = await fetchPublicParcoursSummary(metier).catch(() => []);
  const faq = buildOccupationFaq(profession);
  const url = `${SITE_ORIGIN}/devenir-${metier}`;
  const occupationJsonLd = buildOccupationJsonLd(profession, url);
  const faqJsonLd = faq.length > 0 ? buildFaqPageJsonLd(faq) : null;

  const byNiveau = new Map<string, typeof parcours>();
  for (const p of parcours) {
    const list = byNiveau.get(p.niveau_scolaire) ?? [];
    list.push(p);
    byNiveau.set(p.niveau_scolaire, list);
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      {/* Epic 7 review fix — `serializeJsonLd` escapes `<` (stored XSS via
          admin-editable description/prospects/FAQ text; `lib/seo/json-ld.ts`). */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: serializeJsonLd(occupationJsonLd) }}
      />
      {faqJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: serializeJsonLd(faqJsonLd) }}
        />
      )}

      <h1 className="mb-2 text-2xl font-bold text-text">
        {t("heading", { name: profession.name })}
      </h1>
      <p className="mb-6 text-body text-text-muted">{profession.description}</p>

      {byNiveau.size > 0 && (
        <section aria-labelledby="quels-bacs-title" className="mb-8">
          <h2 id="quels-bacs-title" className="mb-3 text-h3 font-semibold text-text">
            {t("bacsTitle")}
          </h2>
          <div className="flex flex-col gap-4">
            {[...byNiveau.entries()].map(([niveau, rows]) => (
              <div key={niveau} className="rounded-lg border border-border bg-card p-4">
                <h3 className="mb-2 text-body font-semibold text-text">
                  {rows[0]?.label || niveau}
                </h3>
                <ul className="flex flex-col gap-1">
                  {rows
                    .filter((r) => r.target_school_slug)
                    .map((r) => (
                      <li key={r.target_school_slug}>
                        <Link
                          href={`/formations/${r.target_school_slug}`}
                          className="text-body-sm text-primary hover:underline"
                        >
                          {r.target_school_name}
                        </Link>{" "}
                        <span className="text-body-sm text-text-subtle">
                          — {r.target_school_city}
                        </span>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {faq.length > 0 && (
        <section aria-labelledby="faq-title" className="mb-8">
          <h2 id="faq-title" className="mb-3 text-h3 font-semibold text-text">
            {t("faqTitle")}
          </h2>
          <dl className="flex flex-col gap-4">
            {faq.map((entry) => (
              <div key={entry.question}>
                <dt className="font-semibold text-text">{entry.question}</dt>
                <dd className="text-body-sm text-text-muted">{entry.answer}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {/* Epic 7 review fix — the `/{niveau}/quel-bac-pour-{metier}` pages
          (Story 7.3 AC2) were orphans: in no sitemap and linked from
          nowhere, so Google could never discover them. They're now both
          sitemap-declared (`app/sitemap.ts`) and cross-linked from here,
          their natural parent. Rendered inline (not a shared component):
          `src/components/**` is owned by the accessibility workstream. */}
      <nav aria-labelledby="niveau-pages-title" className="mb-8">
        <h2 id="niveau-pages-title" className="mb-3 text-h3 font-semibold text-text">
          {t("niveauPagesTitle")}
        </h2>
        <ul className="flex flex-col gap-1">
          {Object.keys(NIVEAU_SLUGS).map((niveau) => (
            <li key={niveau}>
              <Link
                href={`/${niveau}/quel-bac-pour-${metier}`}
                className="text-body-sm text-primary hover:underline"
              >
                {t("niveauPageLink", {
                  name: profession.name,
                  niveauLabel: tNiveauLabels(niveau),
                })}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <section
        aria-labelledby="signup-cta-title"
        className="rounded-lg border border-border bg-card p-6 text-center"
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
    </main>
  );
}
