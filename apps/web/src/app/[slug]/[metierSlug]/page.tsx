import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchPublicProfession } from "@/lib/api/professions";
import { fetchPublicParcoursSummary } from "@/lib/api/schools";
import {
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

const QUEL_BAC_POUR_PREFIX = "quel-bac-pour-";

function extractMetierSlug(metierSlug: string): string | null {
  return metierSlug.startsWith(QUEL_BAC_POUR_PREFIX)
    ? metierSlug.slice(QUEL_BAC_POUR_PREFIX.length)
    : null;
}

const NIVEAU_SLUGS: Record<string, { apiValue: string; label: string }> = {
  "3eme": { apiValue: "troisieme_bac_pro", label: "3ème" },
  "terminale-generale": { apiValue: "terminale_generale", label: "Terminale Générale" },
  "terminale-technologique": {
    apiValue: "terminale_technologique",
    label: "Terminale Technologique",
  },
  "terminale-pro": { apiValue: "terminale_pro", label: "Terminale Pro" },
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string; metierSlug: string }>;
}) {
  const { slug: niveau, metierSlug } = await params;
  const niveauInfo = NIVEAU_SLUGS[niveau];
  const metier = extractMetierSlug(metierSlug);
  if (!niveauInfo || !metier) return { title: "Quel bac choisir — Path Advisor" };
  try {
    const profession = await fetchPublicProfession(metier);
    const title = `Quel bac pour devenir ${profession.name} depuis la ${niveauInfo.label} ? — Path Advisor`;
    const description = `Quel bac choisir en ${niveauInfo.label} pour devenir ${profession.name} ? Formations et lycées associés.`;
    return {
      title,
      description,
      openGraph: {
        title,
        description,
        url: `${SITE_ORIGIN}/${niveau}/quel-bac-pour-${metier}`,
        type: "website",
      },
      twitter: { card: "summary_large_image", title, description },
    };
  } catch {
    return { title: "Quel bac choisir — Path Advisor" };
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
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(occupationJsonLd) }}
      />
      {faqJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
        />
      )}

      <h1 className="mb-2 text-2xl font-bold text-text">
        Quel bac pour devenir {profession.name} depuis la {niveauInfo.label} ?
      </h1>
      <p className="mb-6 text-body text-text-muted">{profession.description}</p>

      <section aria-labelledby="formations-title" className="mb-8">
        <h2 id="formations-title" className="mb-3 text-h3 font-semibold text-text">
          {niveau === "3eme"
            ? "Lycées professionnels associés"
            : `Formations accessibles depuis la ${niveauInfo.label}`}
        </h2>
        {schoolsForNiveau.length === 0 ? (
          <p className="text-body-sm text-text-muted">
            Aucune formation référencée pour ce niveau pour l&apos;instant.
          </p>
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
            Questions fréquentes
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
          Découvre ton parcours personnalisé
        </h2>
        <p className="mb-4 text-body-sm text-text-muted">
          Crée ton compte gratuit pour construire ton propre parcours vers {profession.name}.
        </p>
        <Link
          href="/auth/signup"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-body-sm font-medium text-primary-foreground hover:opacity-90"
        >
          Créer mon compte gratuit
        </Link>
      </section>
    </main>
  );
}
