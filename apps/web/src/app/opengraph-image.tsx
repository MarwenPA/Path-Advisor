import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "@/lib/seo/og-image";

export const alt = "Path-Advisor — Trouve ta voie, étape par étape";
export const size = OG_IMAGE_SIZE;
export const contentType = OG_IMAGE_CONTENT_TYPE;

export default async function Image() {
  return renderOgImage({
    eyebrow: "Orientation scolaire et professionnelle",
    title: "Trouve ta voie, étape par étape",
  });
}
