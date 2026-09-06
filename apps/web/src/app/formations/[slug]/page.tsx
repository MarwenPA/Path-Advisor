import Link from "next/link";
import { notFound } from "next/navigation";

import { FicheEcole } from "@/components/schools/FicheEcole";
import { ApiError } from "@/lib/api/client";
import { fetchPublicSchool } from "@/lib/api/schools";
import { SITE_ORIGIN, buildEducationalOrganizationJsonLd } from "@/lib/seo/occupation-landing";

/**
 * `/formations/{slug}` — Story 7.2 (SSR fiche école/formation indexable,
 * AC1). Public route (no `(authenticated)` layout) — separate from the
 * existing authenticated `/schools/{slug}` (which stays as-is: different
 * URL, different serializer, includes the premium `<OutreachSection>` this
 * page deliberately omits for anonymous visitors).
 *
 * `revalidate = 3600` — same CDN-cache rationale as Story 7.1's fiche
 * métier page.
 */
export const revalidate = 3600;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const school = await fetchPublicSchool(slug);
    const title = `${school.name} — Path Advisor`;
    const description = school.description.slice(0, 155);
    return {
      title,
      description,
      openGraph: {
        title,
        description,
        url: `${SITE_ORIGIN}/formations/${slug}`,
        type: "website",
      },
      twitter: { card: "summary_large_image", title, description },
    };
  } catch {
    return { title: "École — Path Advisor" };
  }
}

export default async function PublicFormationPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let school;
  try {
    school = await fetchPublicSchool(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
      return null;
    }
    throw err;
  }

  // Story 7.4 AC — EducationalOrganization JSON-LD (rich snippets).
  const educationalOrgJsonLd = buildEducationalOrganizationJsonLd(
    school,
    `${SITE_ORIGIN}/formations/${slug}`,
  );

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(educationalOrgJsonLd) }}
      />
      {/* No public catalog listing page exists yet (out of scope for this
          story — no AC asks for `/formations` index) so there is no "back
          to list" link here, unlike the authenticated `/schools` flow. */}
      <FicheEcole school={school} variant="expanded" />

      {!!school.metiers_cibles?.length && (
        <section aria-labelledby="metiers-cibles-title" className="mt-6">
          <h2 id="metiers-cibles-title" className="mb-2 text-h3 font-semibold text-text">
            Métiers auxquels cette formation mène
          </h2>
          <ul className="flex flex-wrap gap-2">
            {school.metiers_cibles.map((m) => (
              <li key={m.slug}>
                <Link
                  href={`/metiers/${m.slug}`}
                  className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1 text-body-sm text-text hover:bg-muted"
                >
                  {m.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {!!school.similar_schools?.length && (
        <section aria-labelledby="similar-schools-title" className="mt-6">
          <h2 id="similar-schools-title" className="mb-2 text-h3 font-semibold text-text">
            Écoles similaires
          </h2>
          <ul className="flex flex-col gap-1">
            {school.similar_schools.map((s) => (
              <li key={s.slug}>
                <Link
                  href={`/formations/${s.slug}`}
                  className="text-body-sm text-primary hover:underline"
                >
                  {s.name}
                </Link>{" "}
                <span className="text-body-sm text-text-subtle">— {s.city}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section
        aria-labelledby="signup-cta-title"
        className="mt-8 rounded-lg border border-border bg-card p-6 text-center"
      >
        <h2 id="signup-cta-title" className="mb-2 text-h3 font-semibold text-text">
          Découvre tes vraies chances d&apos;admission
        </h2>
        <p className="mb-4 text-body-sm text-text-muted">
          Crée ton compte gratuit pour voir ta probabilité d&apos;admission personnalisée à{" "}
          {school.name}.
        </p>
        <Link
          href="/auth/signup"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-body-sm font-medium text-primary-foreground hover:opacity-90"
        >
          Crée ton compte pour voir ta proba d&apos;admission personnalisée
        </Link>
      </section>
    </main>
  );
}
