import { ImageResponse } from "next/og";

/**
 * Shared 1200×630 Open Graph image renderer — Story 7.5 AC.
 *
 * Sobre branding (brand vermillon `#C8312D`, Story 1.2 tokens) + a
 * contextual title (métier name, école name, etc.) — no font file loaded
 * (`next/og`'s default fallback font renders fine for this simple layout;
 * loading a custom `.ttf` would be extra weight for no visible gain here).
 */
export const OG_IMAGE_SIZE = { width: 1200, height: 630 };
export const OG_IMAGE_CONTENT_TYPE = "image/png";

export function renderOgImage({ eyebrow, title }: { eyebrow: string; title: string }) {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "80px",
        backgroundColor: "#FFFFFF",
        backgroundImage: "linear-gradient(135deg, #FFF5F4 0%, #FFFFFF 60%)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <svg width="56" height="56" viewBox="0 0 64 64" fill="none">
          <path
            d="M10 45.9A26 26 0 1 1 26 57.3"
            stroke="#1A1A1A"
            strokeWidth={4}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="32" cy="32" r="14" stroke="#1A1A1A" strokeWidth={4} />
          <path d="M18 32V61" stroke="#1A1A1A" strokeWidth={4} strokeLinecap="round" />
          <circle cx="32" cy="32" r="6" fill="#C8312D" />
        </svg>
        <div style={{ fontSize: 36, fontWeight: 600, color: "#1A1A1A", letterSpacing: -1 }}>
          Path-Advisor
        </div>
      </div>
      <div style={{ fontSize: 28, color: "#6B6B6B", marginBottom: 16 }}>{eyebrow}</div>
      <div
        style={{
          fontSize: 64,
          fontWeight: 700,
          color: "#1A1A1A",
          lineHeight: 1.15,
          display: "flex",
        }}
      >
        {title}
      </div>
    </div>,
    { ...OG_IMAGE_SIZE },
  );
}
