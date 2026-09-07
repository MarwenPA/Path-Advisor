import type { MetadataRoute } from "next";

import { fetchPublicProfessionSlugs } from "@/lib/api/professions";
import { fetchPublicSchoolSlugs } from "@/lib/api/schools";
import { NIVEAU_SLUGS, SITE_ORIGIN } from "@/lib/seo/occupation-landing";

/**
 * `/sitemap.xml` — Story 7.4 AC. Next.js file convention (`app/sitemap.ts`).
 *
 * Lists every current public URL: fiches métier (`/metiers/{slug}`),
 * fiches école/formation (`/formations/{slug}`), the `/devenir-{metier}`
 * long-tail landing per métier (Story 7.3 AC1), and the niveau-adapted
 * `/{niveau}/quel-bac-pour-{metier}` variants (Story 7.3 AC2). Epic 7
 * review fix: the niveau pages were previously excluded on the theory that
 * "Google discovers linked pages" — but nothing linked to them either, so
 * the whole AC2 deliverable was undiscoverable. They're now enumerated
 * from the same `NIVEAU_SLUGS` map the page validates against (any valid
 * niveau × existing métier renders — never a 404), and `/devenir-{metier}`
 * links to them as well.
 *
 * Not sitemap-index-segmented (AC: "si > 50 000 URLs") — the current
 * referential (professions + schools) is a curated catalog of a few
 * hundred rows, several orders of magnitude below that threshold.
 * Revisit if/when the catalog grows.
 */
// Epic 7 review follow-up: once the slug fetchers stopped forwarding
// cookies (`forwardCookies: false`), this route became statically
// prerenderable — but the Docker image build has no reachable API, so a
// static sitemap would be baked EMPTY forever (the `.catch(() => [])`
// below would eat the build-time failure silently). Force per-request
// rendering instead; crawlers hit /sitemap.xml rarely, so no cache needed.
export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [professions, schools] = await Promise.all([
    fetchPublicProfessionSlugs().catch(() => []),
    fetchPublicSchoolSlugs().catch(() => []),
  ]);

  const staticEntries: MetadataRoute.Sitemap = [
    { url: SITE_ORIGIN, changeFrequency: "weekly", priority: 1.0 },
  ];

  const metierEntries: MetadataRoute.Sitemap = professions.map((p) => ({
    url: `${SITE_ORIGIN}/metiers/${p.slug}`,
    lastModified: p.updated_at,
    changeFrequency: "monthly",
    priority: 0.8,
  }));

  const devenirEntries: MetadataRoute.Sitemap = professions.map((p) => ({
    url: `${SITE_ORIGIN}/devenir-${p.slug}`,
    lastModified: p.updated_at,
    changeFrequency: "monthly",
    priority: 0.7,
  }));

  const niveauEntries: MetadataRoute.Sitemap = professions.flatMap((p) =>
    Object.keys(NIVEAU_SLUGS).map((niveau) => ({
      url: `${SITE_ORIGIN}/${niveau}/quel-bac-pour-${p.slug}`,
      lastModified: p.updated_at,
      changeFrequency: "monthly" as const,
      priority: 0.6,
    })),
  );

  const formationEntries: MetadataRoute.Sitemap = schools.map((s) => ({
    url: `${SITE_ORIGIN}/formations/${s.slug}`,
    lastModified: s.updated_at,
    changeFrequency: "monthly",
    priority: 0.7,
  }));

  return [
    ...staticEntries,
    ...metierEntries,
    ...devenirEntries,
    ...niveauEntries,
    ...formationEntries,
  ];
}
