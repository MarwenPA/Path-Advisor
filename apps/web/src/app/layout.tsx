import type { Metadata } from "next";
import localFont from "next/font/local";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import "./globals.css";

import { QueryProvider } from "@/components/providers/query-provider";
import { SITE_ORIGIN } from "@/lib/seo/occupation-landing";

// Story 7.11 — self-hosted SUBSET of Inter variable, replacing
// `Inter({ subsets: ["latin"] })` from next/font/google.
//
// Why: the Google "latin" build weighed 48.4KB and sat on the LCP critical
// path; measured (Story 7.9, display:"optional" experiment) it was worth
// ~400ms of simulated LCP on the fiche pages and explained their whole
// 2105ms-vs-2500ms bimodality. This file is 26.2KB (-46%) with ZERO glyph
// regression: the wght axis is limited to 400:700 (the only weights the app
// uses — grep font-normal/medium/semibold/bold) and the glyph set to the
// characters French UI + referential data actually render. Chars absent
// here (←, →, Ÿ, ﬁ/ﬂ) were verified ABSENT from the Google build too — the
// catalog's arrows have always rendered from the system fallback.
//
// Regeneration pipeline (documented in story 7-11, run from anywhere):
//   uvx --from "fonttools[woff]" fonttools varLib.instancer inter.woff2 \
//     wght=400:700 -o inter-wght.woff2
//   uvx --from "fonttools[woff]" pyftsubset inter-wght.woff2 \
//     --unicodes="U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+0178,U+02C6,\
//       U+02DA,U+02DC,U+2000-2015,U+2018-201F,U+2020-2027,U+2030-203A,\
//       U+205F,U+20AC,U+2122,U+2190-2193,U+2212,U+2215" \
//     --layout-features='kern,liga,calt,ccmp,mark,mkmk,locl,tnum,case' \
//     --flavor=woff2 --output-file=inter-vf-latin-fr.woff2
//
// `display: "swap"` is kept deliberately: "optional" would drop the brand
// typeface on first visit over slow connections (a design trade-off we
// declined — story 7-11 §2). Preload and `adjustFontFallback` (fallback
// metrics matching, no CLS on swap) are next/font/local defaults.
const inter = localFont({
  src: "./fonts/inter-vf-latin-fr.woff2",
  weight: "400 700",
  variable: "--font-inter",
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
  //
  // Revue Epic 8 (perf) : ce provider est sérialisé dans CHAQUE page,
  // publiques comprises — celles du gate LCP 2500 ms. Les namespaces
  // consommés uniquement côté authentifié en sont exclus ici et re-fournis
  // par le provider de `(authenticated)/layout.tsx`. Un namespace ajouté à
  // fr.json pour l'espace connecté doit rejoindre AUTH_ONLY_NAMESPACES,
  // sinon il taxe le LCP des pages publiques.
  const messages = await getMessages();
  const AUTH_ONLY_NAMESPACES = ["accueil", "deltaRecap", "calendarNotification"] as const;
  const publicMessages = Object.fromEntries(
    Object.entries(messages).filter(([ns]) => !AUTH_ONLY_NAMESPACES.includes(ns as never)),
  );

  return (
    <html lang="fr" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <NextIntlClientProvider messages={publicMessages}>
          <QueryProvider>{children}</QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
