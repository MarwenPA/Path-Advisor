import type { MetadataRoute } from "next";

import { fetchPublicProfessionSlugs } from "@/lib/api/professions";
import { fetchPublicSchoolSlugs } from "@/lib/api/schools";
import { SITE_ORIGIN } from "@/lib/seo/occupation-landing";

/**
 * `/sitemap.xml` — Story 7.4 AC. Next.js file convention (`app/sitemap.ts`).
 *
 * Lists every current public URL: fiches métier (`/metiers/{slug}`),
 * fiches école/formation (`/formations/{slug}`), and the `/devenir-{metier}`
 * long-tail landing per métier (Story 7.3). The niveau-adapted
 * `/{niveau}/quel-bac-pour-{metier}` variant is intentionally NOT
 * enumerated here — with 4 niveaux × every métier it would multiply the
 * sitemap size for pages whose content is mostly a subset of the
 * `/devenir-{metier}` page (same profession fiche + same FAQ), and Google
 * discovers linked pages from crawled ones regardless (the `/devenir-*`
 * page doesn't currently link into it, but the niveau pages themselves are
 * still indexable/crawlable directly — just not sitemap-declared).
 *
 * Not sitemap-index-segmented (AC: "si > 50 000 URLs") — the current
 * referential (professions + schools) is a curated catalog of a few
 * hundred rows, several orders of magnitude below that threshold.
 * Revisit if/when the catalog grows.
 */
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

  const formationEntries: MetadataRoute.Sitemap = schools.map((s) => ({
    url: `${SITE_ORIGIN}/formations/${s.slug}`,
    lastModified: s.updated_at,
    changeFrequency: "monthly",
    priority: 0.7,
  }));

  return [...staticEntries, ...metierEntries, ...devenirEntries, ...formationEntries];
}
