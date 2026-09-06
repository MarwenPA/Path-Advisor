import { fetchPublicProfession } from "@/lib/api/professions";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const alt = "Quel bac choisir — Path-Advisor";
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
