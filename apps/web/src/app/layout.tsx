import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import "./globals.css";

import { QueryProvider } from "@/components/providers/query-provider";
import { SITE_ORIGIN } from "@/lib/seo/occupation-landing";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

// Epic 7 review fixes:
// - `metadataBase` was missing entirely — Next.js resolves the
//   file-convention `opengraph-image.tsx` URLs against it, so in this
//   self-hosted Docker deploy every `og:image`/`twitter:image` pointed at
//   `http://localhost:3000/...` in production (no share preview worked
//   anywhere). It also lets `alternates.canonical` use relative paths.
// - the fallback `description` was hardcoded ENGLISH marketing copy on a
//   French-facing product — moved to `messages/fr.json#common` (Story 7.7
//   convention), hence `generateMetadata` instead of a static export.
export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("common");
  return {
    metadataBase: new URL(SITE_ORIGIN),
    title: t("rootMetaTitle"),
    description: t("rootMetaDescription"),
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Story 7.7 — single-locale (`fr`) messages, loaded server-side and
  // handed to the client provider (`src/i18n/request.ts` resolves the
  // catalog; no `[locale]` segment to read here, see `src/i18n/config.ts`).
  const messages = await getMessages();

  return (
    <html lang="fr" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <NextIntlClientProvider messages={messages}>
          <QueryProvider>{children}</QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
