/**
 * Back-office layout — Epic 9. Route-guarded `path_admin` only
 * (`route-guards.ts`); the API re-checks `IsPathAdmin` + MFA on every call,
 * this chrome is navigation, never a security boundary.
 *
 * Sections appear as their story ships: Métiers (9.1), Écoles + Calendrier
 * (9.2), Signalements (9.3), Modération (9.4).
 */

import Link from "next/link";
import { getTranslations } from "next-intl/server";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const t = await getTranslations("admin");
  const sections = [
    { href: "/admin/metiers", label: t("nav.metiers") },
    { href: "/admin/ecoles", label: t("nav.ecoles") },
    { href: "/admin/calendrier", label: t("nav.calendrier") },
    { href: "/admin/signalements", label: t("nav.signalements") },
    { href: "/admin/moderation", label: t("nav.moderation") },
  ];

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      <header className="mb-6 flex flex-col gap-3">
        <h1 className="text-2xl font-bold text-text">{t("title")}</h1>
        <nav aria-label={t("navLabel")} className="flex flex-wrap gap-2">
          {sections.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm font-medium text-text hover:bg-bg-2"
            >
              {section.label}
            </Link>
          ))}
        </nav>
      </header>
      {children}
    </div>
  );
}
