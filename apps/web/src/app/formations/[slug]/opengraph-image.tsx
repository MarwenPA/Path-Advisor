import { fetchPublicSchool } from "@/lib/api/schools";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

/** Epic 7 review fix — per-école alt instead of a static generic one; see
 * `metiers/[slug]/opengraph-image.tsx`. */
export async function generateImageMetadata({ params }: { params?: Promise<{ slug: string }> }) {
  // `params` is undefined during `next build`'s page-data collection pass
  // (no static params for this segment) — fall back to the generic alt.
  const { slug } = (await params) ?? {};
  let alt = "Fiche école — Path-Advisor";
  try {
    if (slug) {
      const school = await fetchPublicSchool(slug);
      alt = `Fiche école ${school.name} — Path-Advisor`;
    }
  } catch {
    // Generic fallback — must never throw (see the renderer below).
  }
  return [{ id: "og", alt, size: OG_IMAGE_SIZE, contentType: OG_IMAGE_CONTENT_TYPE }];
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let title = "Fiche école";
  try {
    const school = await fetchPublicSchool(slug);
    title = school.name;
  } catch {
    // Graceful fallback — see metiers/[slug]/opengraph-image.tsx.
  }
  return renderOgImage({ eyebrow: "Fiche école / formation", title });
}
