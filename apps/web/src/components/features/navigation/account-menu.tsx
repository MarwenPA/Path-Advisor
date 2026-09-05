"use client";

/**
 * Account menu — Story 1.15 (UX-DR31).
 *
 * Single entry point for "who am I / where do I manage my account / how do I
 * leave" — shared by `DesktopSidebar` and `MobileNav` so the logout logic
 * lives in exactly one place. No `@radix-ui/react-dropdown-menu` dependency
 * (not in the repo yet, cf. story Dev Notes) — a two-item menu doesn't
 * justify the addition, so this is a small hand-rolled popover with
 * click-outside + Escape + focus-return.
 *
 * Deliberately NOT `role="menu"`/`role="menuitem"` (code-review fix,
 * 2026-09): that ARIA pattern promises arrow-key/Home/End navigation and a
 * roving tabindex, which this component doesn't implement — advertising it
 * without the behavior is worse for screen-reader users than a plain
 * disclosure popover (`aria-expanded` on the trigger + regular
 * links/buttons, which Tab already reaches in order).
 */
import { LogOut, Settings } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { logoutUser } from "@/lib/api/auth";
import { cn } from "@/lib/utils";

/** Kept local rather than reusing `MVP_FALLBACK_PATH` — that constant means
 * "post-login fallback for roles without a dashboard" and happens to equal
 * this today, but the two are conceptually different and must be free to
 * diverge (code-review fix, 2026-09). */
const SETTINGS_PATH = "/parametres/confidentialite";

export interface AccountMenuProps {
  email: string;
  /** "sidebar" renders a wide trigger with the email visible; "compact" (mobile) is icon-only. */
  variant?: "sidebar" | "compact";
  /**
   * Which way the popover opens relative to the trigger. Callers near the
   * bottom of the viewport (the mobile bottom tab bar) MUST pass "up" — a
   * downward popover there renders below the viewport edge and is
   * unreachable (code-review fix, 2026-09: this shipped broken for the
   * tab-bar instance because the default was hard-coded downward).
   */
  placement?: "up" | "down";
}

function initialOf(email: string): string {
  return email.trim().charAt(0).toUpperCase() || "?";
}

export function AccountMenu({ email, variant = "sidebar", placement = "down" }: AccountMenuProps) {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node;
      if (popoverRef.current?.contains(target) || triggerRef.current?.contains(target)) return;
      setOpen(false);
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  async function handleLogout() {
    setOpen(false);
    try {
      await logoutUser();
    } catch {
      // Code-review note: a network failure on logout must not trap the
      // user on a page they believe they've left — the session cookie will
      // expire server-side regardless. Redirect unconditionally.
    }
    // `replace` (not `push`) + `refresh()` (code-review fix, 2026-09): a
    // plain `push` leaves the authenticated shell in the client Router
    // Cache, so pressing Back after logout could re-render the nav/email
    // from cache instead of hitting the server layout's auth guard again —
    // exactly the "stale session on a shared machine" risk AC3 exists to
    // prevent.
    router.replace("/auth/login");
    router.refresh();
  }

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className={cn(
          "flex items-center gap-2 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          variant === "sidebar" ? "w-full p-2 hover:bg-muted" : "p-2",
        )}
      >
        <span
          aria-hidden="true"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-semibold text-white"
        >
          {initialOf(email)}
        </span>
        {variant === "sidebar" ? (
          <span className="min-w-0 flex-1 truncate text-body-sm text-text">{email}</span>
        ) : (
          <span className="sr-only">Mon compte ({email})</span>
        )}
      </button>

      {open ? (
        <div
          ref={popoverRef}
          data-testid="account-menu-popover"
          className={cn(
            "absolute z-50 min-w-48 rounded-lg border border-border bg-card p-1 shadow-md",
            variant === "sidebar" ? "left-0" : "right-0",
            placement === "up" ? "bottom-full mb-2" : "top-full mt-2",
          )}
        >
          <div className="truncate px-3 py-2 text-caption text-text-muted">{email}</div>
          <Link
            href={SETTINGS_PATH}
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-md px-3 py-2 text-body-sm text-text hover:bg-muted"
          >
            <Settings className="h-4 w-4" aria-hidden="true" />
            Paramètres
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-body-sm text-danger hover:bg-muted"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Déconnexion
          </button>
        </div>
      ) : null}
    </div>
  );
}
