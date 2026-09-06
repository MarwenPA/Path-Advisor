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
 * `/{niveau}/quel-bac-pour-{metier}` — Story 7.3 AC2 (niveau-adapted
 * long-tail landing).
 *
 * Code-review fix (same class of bug as the sibling `/devenir-{metier}`
 * route, see `app/[slug]/page.tsx`'s docstring): Next.js dynamic segments
 * can't glue a literal prefix onto a bracket (`quel-bac-pour-[metier]`
 * doesn't work — confirmed by a live 404 during the Docker smoke test).
 * This folder is `[metierSlug]` (fully dynamic) and the "quel-bac-pour-"
 * prefix is parsed out of it in code instead.
 *
 * The parent segment is `[slug]` (not `[niveau]`) for the same reason:
 * Next.js requires every dynamic folder at one route level to share a
 * param name, and the sibling `/devenir-{metier}` route already claims
 * `[slug]` there. `slug` holds the niveau value; renamed to `niveau`
 * locally for readability. `niveau` is validated against
 * `Parcours.NiveauScolaire` (Story 4.7) — the AC's own example ("3ème")
 * maps to `troisieme_bac_pro`, the only 3ème-level pathway the
 * referential models (see `NIVEAU_SLUGS` below for the full scope
 * decision).
 */
export const revalidate = 3600;

// Epic 7 review fix — enables ISR; see `/metiers/[slug]/page.tsx` for why
// this returns `[]` instead of fetching all combinations at build time.
export function generateStaticParams(): { slug: string; metierSlug: string }[] {
  return [];
}

const QUEL_BAC_POUR_PREFIX = "quel-bac-pour-";

function extractMetierSlug(metierSlug: string): string | null {
  return metierSlug.startsWith(QUEL_BAC_POUR_PREFIX)
    ? metierSlug.slice(QUEL_BAC_POUR_PREFIX.length)
    : null;
}

// Story 7.7 — niveau *labels* live in `messages/fr.json#quelBacPourPage.niveauLabels`
// (keyed by the same niveau slug). Epic 7 review fix: the slug→enum map
// itself moved to `lib/seo/occupation-landing.ts` (`NIVEAU_SLUGS`) so
// `app/sitemap.ts` enumerates exactly the slugs this page accepts —
// keeping a second copy here risked sitemap entries that 404.

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string; metierSlug: string }>;
}) {
  const { slug: niveau, metierSlug } = await params;
  const niveauInfo = NIVEAU_SLUGS[niveau];
  const metier = extractMetierSlug(metierSlug);
  const t = await getTranslations("quelBacPourPage");
  if (!niveauInfo || !metier) return { title: t("metaTitleFallback") };
  try {
    const profession = await fetchPublicProfession(metier);
    const niveauLabel = t(`niveauLabels.${niveau}`);
    const title = t("metaTitle", { name: profession.name, niveauLabel });
    const description = t("metaDescription", { name: profession.name, niveauLabel });
    return {
      title,
      description,
      // Epic 7 review fix — explicit canonical (relative, resolved against
      // the root layout's `metadataBase`); see `/devenir-{metier}`.
      alternates: { canonical: `/${niveau}/quel-bac-pour-${metier}` },
      openGraph: {
        title,
        description,
        url: `${SITE_ORIGIN}/${niveau}/quel-bac-pour-${metier}`,
        type: "website",
      },
      twitter: { card: "summary_large_image", title, description },
    };
  } catch {
    return { title: t("metaTitleFallback") };
  }
}

export default async function QuelBacPourMetierPage({
  params,
}: {
  params: Promise<{ slug: string; metierSlug: string }>;
}) {
  const { slug: niveau, metierSlug } = await params;
  const niveauInfo = NIVEAU_SLUGS[niveau];
  const metier = extractMetierSlug(metierSlug);
  if (!niveauInfo || !metier) {
    notFound();
    return null;
  }
  const t = await getTranslations("quelBacPourPage");
  const niveauLabel = t(`niveauLabels.${niveau}`);

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

  const parcours = await fetchPublicParcoursSummary(metier, niveauInfo.apiValue).catch(() => []);
  const faq = buildOccupationFaq(profession);
  const url = `${SITE_ORIGIN}/${niveau}/quel-bac-pour-${metier}`;
  const occupationJsonLd = buildOccupationJsonLd(profession, url);
  const faqJsonLd = faq.length > 0 ? buildFaqPageJsonLd(faq) : null;
  const schoolsForNiveau = parcours.filter((p) => p.target_school_slug);

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
        {t("heading", { name: profession.name, niveauLabel })}
      </h1>
      <p className="mb-6 text-body text-text-muted">{profession.description}</p>

      <section aria-labelledby="formations-title" className="mb-8">
        <h2 id="formations-title" className="mb-3 text-h3 font-semibold text-text">
          {niveau === "3eme"
            ? t("formationsTitleTroisieme")
            : t("formationsTitleOther", { niveauLabel })}
        </h2>
        {schoolsForNiveau.length === 0 ? (
          <p className="text-body-sm text-text-muted">{t("noFormationsYet")}</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {schoolsForNiveau.map((p) => (
              <li key={p.target_school_slug}>
                <Link
                  href={`/formations/${p.target_school_slug}`}
                  className="text-body-sm text-primary hover:underline"
                >
                  {p.target_school_name}
                </Link>{" "}
                <span className="text-body-sm text-text-subtle">— {p.target_school_city}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

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
