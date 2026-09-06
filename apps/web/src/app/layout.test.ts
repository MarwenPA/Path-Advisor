/**
 * Root layout metadata tests — Epic 7 review fixes (`metadataBase` +
 * French fallback description).
 */
import { describe, expect, it, vi } from "vitest";

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));
// `next/font/google` needs the Next compiler — stub it for a metadata-only test.
vi.mock("next/font/google", () => ({
  Inter: () => ({ variable: "--font-inter" }),
}));

import { generateMetadata } from "./layout";

describe("root layout metadata", () => {
  it("sets metadataBase so file-convention og:image URLs resolve to the real origin", async () => {
    const metadata = await generateMetadata();
    // Without this, every og:image/twitter:image resolved to
    // http://localhost:3000/... in the self-hosted production deploy.
    expect(new URL(String(metadata.metadataBase)).origin).toBe("https://path-advisor.fr");
  });

  it("uses a French fallback description from the i18n catalog (not the old English copy)", async () => {
    const metadata = await generateMetadata();
    expect(metadata.title).toBe("Path-Advisor");
    expect(metadata.description).toContain("orientation");
    expect(metadata.description).not.toContain("career-orientation platform");
  });
});
