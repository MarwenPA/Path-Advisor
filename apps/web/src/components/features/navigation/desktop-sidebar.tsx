"use client";

/**
 * Desktop sidebar — Story 1.15 (UX-DR31), `≥ lg` (1024px).
 *
 * Client Component: needs `usePathname()` for the active-item state and
 * renders `AccountMenu` (itself a Client Component). Fixed left, 224px, per
 * the "Side nav fixed left" spec in the UX design doc's Navigation Patterns
 * section.
 */
import Link from "next/link";
import { usePathname } from "next/navigation";

import type { UserRole } from "@/lib/api/auth";
import { getPostLoginPath } from "@/lib/auth/post-login-redirect";
import { NAV_ITEMS } from "@/lib/auth/nav-items";
import { cn } from "@/lib/utils";

import { AccountMenu } from "./account-menu";

export interface DesktopSidebarProps {
  role: UserRole;
  email: string;
}

export function DesktopSidebar({ role, email }: DesktopSidebarProps) {
  const pathname = usePathname();
  const items = NAV_ITEMS[role];
  // `status` doesn't affect the logo destination for an already-authenticated
  // user landing on any role's dashboard — pass a placeholder status literal
  // that resolves the same for every role's happy path.
  const homeHref = getPostLoginPath(role, "active");

  return (
    <nav
      aria-label="Navigation principale"
      className="hidden w-56 shrink-0 flex-col border-r border-border bg-card lg:flex"
    >
      <Link href={homeHref} className="px-4 py-5 text-h3 font-bold text-text">
        Path Advisor
      </Link>

      <ul className="flex flex-1 flex-col gap-1 px-2">
        {items.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          const linkClassName = cn(
            "flex items-center gap-3 rounded-lg border-l-2 border-transparent px-3 py-2 text-body-sm text-text hover:bg-muted",
            isActive && "border-brand bg-bg-2 font-medium",
          );

          if (item.external) {
            return (
              <li key={item.href}>
                <a
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={linkClassName}
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  {item.label}
                </a>
              </li>
            );
          }

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={linkClassName}
              >
                <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="border-t border-border p-2">
        <AccountMenu email={email} variant="sidebar" />
      </div>
    </nav>
  );
}
