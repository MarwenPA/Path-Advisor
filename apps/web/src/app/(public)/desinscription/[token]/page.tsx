/**
 * /desinscription/[token] — Story 8.2 §AC3 (public one-click unsubscribe).
 *
 * PUBLIC page (no auth — the signed token in the URL IS the claim), reached
 * from the legal footer link of every category email. The page only ever
 * EXPLAINS on load; the POST fires on the confirm button click, NEVER on
 * page load — email-client prefetchers follow links, and a GET must not
 * unsubscribe anyone (which is also why the API is POST-only).
 *
 * Route note: `desinscription` is a literal first segment, so this route
 * wins over the top-level `/[slug]/[metierSlug]` SEO catch-alls (verified
 * against the build route table, not assumed).
 */
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { UnsubscribeConfirm } from "./unsubscribe-confirm";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("notifications.unsubscribe");
  return {
    title: t("metaTitle"),
    description: t("metaDescription"),
    // Tokenized utility page — never index (same as cancel-deletion).
    robots: { index: false, follow: false },
  };
}

interface PageProps {
  params: Promise<{ token: string }>;
}

export default async function DesinscriptionPage({ params }: PageProps) {
  const { token } = await params;
  const t = await getTranslations("notifications.unsubscribe");

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-6 px-4 py-12">
      <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">{t("title")}</h1>
      <UnsubscribeConfirm token={token} />
    </main>
  );
}
