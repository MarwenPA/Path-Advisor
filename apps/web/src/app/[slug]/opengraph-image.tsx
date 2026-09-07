import { fetchPublicProfession } from "@/lib/api/professions";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

const DEVENIR_PREFIX = "devenir-";

/** Mirrors `[slug]/page.tsx`'s `extractMetierSlug` — kept local (not
 * imported from the page module) since Next.js image-convention files are
 * compiled as separate route handlers. */
function extractMetierSlug(slug: string): string | null {
  return slug.startsWith(DEVENIR_PREFIX) ? slug.slice(DEVENIR_PREFIX.length) : null;
}

/** Epic 7 review fix — per-métier alt instead of a static generic one; see
 * `metiers/[slug]/opengraph-image.tsx`. */
export async function generateImageMetadata({ params }: { params?: Promise<{ slug: string }> }) {
  // `params` is undefined during `next build`'s page-data collection pass
  // (no static params for this segment) — fall back to the generic alt.
  const { slug } = (await params) ?? {};
  const metier = slug ? extractMetierSlug(slug) : null;
  let alt = "Devenir — Path-Advisor";
  if (metier) {
    try {
      const profession = await fetchPublicProfession(metier);
      alt = `Devenir ${profession.name} — Path-Advisor`;
    } catch {
      // Generic fallback — must never throw (see the renderer below).
    }
  }
  return [{ id: "og", alt, size: OG_IMAGE_SIZE, contentType: OG_IMAGE_CONTENT_TYPE }];
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const metier = extractMetierSlug(slug);
  let title = "Devenir...";
  if (metier) {
    try {
      const profession = await fetchPublicProfession(metier);
      title = `Devenir ${profession.name}`;
    } catch {
      // Graceful fallback — see metiers/[slug]/opengraph-image.tsx.
    }
  }
  return renderOgImage({ eyebrow: "Guide d'orientation", title });
}
