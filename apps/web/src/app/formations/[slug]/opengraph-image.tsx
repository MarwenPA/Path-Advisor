import { fetchPublicSchool } from "@/lib/api/schools";
import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const alt = "Fiche école — Path-Advisor";
export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

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
