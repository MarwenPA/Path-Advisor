/**
 * /parametres/notifications — Story 8.2 §AC1.
 *
 * One toggle per notification category (the 4 backend categories), saved
 * immediately per change — no "save" button. Category labels come from the
 * API (backend French labels, `NotificationCategory.choices`); page chrome
 * strings live in `messages/fr.json#notifications.settings` (Story 7.7
 * conventions).
 */
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { NotificationPreferencesList } from "./notification-preferences-list";
import { fetchNotificationPreferences } from "@/lib/api/notifications";

// Authenticated per-user data — same rationale as /parametres/abonnement.
export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("notifications.settings");
  return {
    title: t("metaTitle"),
    description: t("metaDescription"),
  };
}

export default async function NotificationsPage() {
  const t = await getTranslations("notifications.settings");
  const { preferences } = await fetchNotificationPreferences();

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">{t("title")}</h1>
        <p className="text-body text-text-muted">{t("intro")}</p>
      </header>

      <NotificationPreferencesList initialPreferences={preferences} />
    </main>
  );
}
