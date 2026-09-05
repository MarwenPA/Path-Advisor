"use client";

/**
 * Mobile nav — Story 1.15 (UX-DR31), `< lg` (1024px).
 *
 * Two shapes depending on `hasBottomTabBar(role)`:
 * - `student` (≥ 2 metier items): fixed bottom tab bar, items + account icon,
 *   per "Bottom tab bar 5 onglets max" in the UX design doc.
 * - Every other role today (0-1 metier items): a single icon next to a tab
 *   bar reads as broken, so instead a sticky header with the section title
 *   + account icon on the right (see Navigation Multi-Rôle addendum).
 *
 * Code-review fix (2026-09): the header shape used to render ONLY the
 * account icon, dropping the role's one nav item entirely — a `parent` (or
 * `path_admin`) navigating away from their single page (e.g. to
 * `/parametres`) had no way back except the account menu. The header now
 * also renders that item (icon-only, external-aware) next to the title.
 */
import Link from "next/link";
import { usePathname } from "next/navigation";

import type { UserRole } from "@/lib/api/auth";
import { hasBottomTabBar, NAV_ITEMS } from "@/lib/auth/nav-items";
import { cn } from "@/lib/utils";

import { AccountMenu } from "./account-menu";

export interface MobileNavProps {
  role: UserRole;
  email: string;
}

export function MobileNav({ role, email }: MobileNavProps) {
  const pathname = usePathname();
  const items = NAV_ITEMS[role];

  if (!hasBottomTabBar(role)) {
    const current = items.find(
      (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
    );
    return (
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-border bg-card px-4 py-3 lg:hidden">
        <span className="text-h3 font-semibold text-text">{current?.label ?? "Path Advisor"}</span>
        <div className="flex items-center gap-1">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = current?.href === item.href;
            const className = cn(
              "flex h-10 w-10 items-center justify-center rounded-lg",
              isActive ? "text-brand" : "text-text-muted",
            );
            return item.external ? (
              <a
                key={item.href}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={item.label}
                className={className}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </a>
            ) : (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={isActive ? "page" : undefined}
                className={className}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </Link>
            );
          })}
          <AccountMenu email={email} variant="compact" placement="down" />
        </div>
      </header>
    );
  }

  return (
    <nav
      aria-label="Navigation principale"
      className="fixed inset-x-0 bottom-0 z-40 flex items-stretch justify-around border-t border-border bg-card lg:hidden"
    >
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "flex min-h-[44px] min-w-[44px] flex-1 flex-col items-center justify-center gap-0.5 py-2 text-caption",
              isActive ? "text-brand" : "text-text-muted",
            )}
          >
            <Icon
              className="h-5 w-5"
              aria-hidden="true"
              fill={isActive ? "currentColor" : "none"}
            />
            {item.label}
          </Link>
        );
      })}
      <div className="flex min-h-[44px] min-w-[44px] flex-1 flex-col items-center justify-center py-2">
        {/* Code-review fix (2026-09): "up" — this trigger sits in a
            `fixed bottom-0` bar, so the popover's previous downward default
            rendered below the viewport edge and was unreachable. */}
        <AccountMenu email={email} variant="compact" placement="up" />
      </div>
    </nav>
  );
}
