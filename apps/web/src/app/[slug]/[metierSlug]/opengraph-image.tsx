import { fetchPublicProfession } from "@/lib/api/professions";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

const QUEL_BAC_POUR_PREFIX = "quel-bac-pour-";

/** Mirrors `[slug]/[metierSlug]/page.tsx`'s `extractMetierSlug` — kept
 * local, see `[slug]/opengraph-image.tsx` for why. */
function extractMetierSlug(metierSlug: string): string | null {
  return metierSlug.startsWith(QUEL_BAC_POUR_PREFIX)
    ? metierSlug.slice(QUEL_BAC_POUR_PREFIX.length)
    : null;
}

/** Epic 7 review fix — per-métier alt instead of a static generic one; see
 * `metiers/[slug]/opengraph-image.tsx`. */
export async function generateImageMetadata({
  params,
}: {
  params?: Promise<{ slug: string; metierSlug: string }>;
}) {
  // `params` is undefined during `next build`'s page-data collection pass
  // (no static params for this segment) — fall back to the generic alt.
  const { metierSlug } = (await params) ?? {};
  const metier = metierSlug ? extractMetierSlug(metierSlug) : null;
  let alt = "Quel bac choisir — Path-Advisor";
  if (metier) {
    try {
      const profession = await fetchPublicProfession(metier);
      alt = `Quel bac pour devenir ${profession.name} — Path-Advisor`;
    } catch {
      // Generic fallback — must never throw (see the renderer below).
    }
  }
  return [{ id: "og", alt, size: OG_IMAGE_SIZE, contentType: OG_IMAGE_CONTENT_TYPE }];
}

export default async function Image({
  params,
}: {
  params: Promise<{ slug: string; metierSlug: string }>;
}) {
  const { metierSlug } = await params;
  const metier = extractMetierSlug(metierSlug);
  let title = "Quel bac choisir ?";
  if (metier) {
    try {
      const profession = await fetchPublicProfession(metier);
      title = `Quel bac pour devenir ${profession.name} ?`;
    } catch {
      // Graceful fallback — see metiers/[slug]/opengraph-image.tsx.
    }
  }
  return renderOgImage({ eyebrow: "Guide d'orientation", title });
}
