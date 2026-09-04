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
        <AccountMenu email={email} variant="compact" />
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
        <AccountMenu email={email} variant="compact" />
      </div>
    </nav>
  );
}
