import { fetchPublicProfession } from "@/lib/api/professions";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

/**
 * Epic 7 review fix — the static `export const alt` was a generic
 * "Fiche métier — Path-Advisor" for every métier. `generateImageMetadata`
 * is the Next.js mechanism for a per-params alt: it names the actual
 * profession (screen readers / previews on the shared card).
 * `fetchPublicProfession` is `React.cache()`-wrapped, so the extra call
 * here dedupes with the image renderer's within one render.
 */
export async function generateImageMetadata({ params }: { params?: Promise<{ slug: string }> }) {
  // `params` is undefined during `next build`'s page-data collection pass
  // (no static params for this segment) — fall back to the generic alt.
  const { slug } = (await params) ?? {};
  let alt = "Fiche métier — Path-Advisor";
  try {
    if (slug) {
      const profession = await fetchPublicProfession(slug);
      alt = `Fiche métier ${profession.name} — Path-Advisor`;
    }
  } catch {
    // Generic fallback — must never throw (see the renderer below).
  }
  return [{ id: "og", alt, size: OG_IMAGE_SIZE, contentType: OG_IMAGE_CONTENT_TYPE }];
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let title = "Fiche métier";
  try {
    const profession = await fetchPublicProfession(slug);
    title = profession.name;
  } catch {
    // Graceful fallback — the page itself 404s on an unknown slug; this
    // image is never actually served for that case, but must not throw.
  }
  return renderOgImage({ eyebrow: "Fiche métier", title });
}
