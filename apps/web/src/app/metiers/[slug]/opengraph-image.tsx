import { fetchPublicProfession } from "@/lib/api/professions";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const alt = "Fiche métier — Path-Advisor";
export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

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
