"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Toast, useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

/**
 * `SideFlow` — Story 10.6 (UX-DR18).
 *
 * Persistent, NON-blocking banner for critical confirmations that must not
 * interrupt the current exploration (parental consent pending, payment
 * confirmation in flight, …). Deliberate contrasts with a dialog:
 *
 *  - `role="status"` + polite live region, never `role="dialog"`: no focus
 *    trap, no scroll lock, no Escape handling — the page behind stays fully
 *    usable (AC "l'exploration reste possible sans validation immédiate").
 *  - Resolution is a state change, not a user action: when `open` flips from
 *    true to false and `resolvedMessage` is set, the banner disappears and a
 *    toast confirms (AC "le bandeau disparaît + un toast confirme"). A first
 *    render with `open=false` shows nothing — the toast only fires on a
 *    transition actually witnessed by the user.
 *  - Tone: the message informs without blaming; the CTA is secondary and
 *    optional. Copy is provided by the instance and must pass the calm-tone
 *    lint (`lib/i18n/tone.test.ts`).
 *
 * `position="top"` renders in-flow (mount under the nav banners in the
 * authenticated layout). `position="bottom"` is fixed and sits above the
 * mobile bottom tab bar (64px — cf. layout `pb-16`), flush on `lg:`.
 */
export interface SideFlowCta {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export interface SideFlowProps {
  open: boolean;
  message: string;
  /** Optional secondary action ("Relancer mon parent", …). */
  cta?: SideFlowCta;
  /** Inline feedback zone next to the CTA (sent / rate-limited / error). */
  feedback?: React.ReactNode;
  position?: "top" | "bottom";
  /** Toast text confirming resolution when `open` transitions true → false. */
  resolvedMessage?: string;
}

export function SideFlow({
  open,
  message,
  cta,
  feedback,
  position = "top",
  resolvedMessage,
}: SideFlowProps) {
  const { message: toastMessage, showToast } = useToast();
  const wasOpen = React.useRef(false);

  React.useEffect(() => {
    if (wasOpen.current && !open && resolvedMessage) {
      showToast(resolvedMessage, 6000);
    }
    wasOpen.current = open;
  }, [open, resolvedMessage, showToast]);

  return (
    <>
      <Toast message={toastMessage} />
      {open && (
        <div
          role="status"
          aria-live="polite"
          className={cn(
            "flex flex-wrap items-center justify-between gap-3 bg-bg-2 px-4 py-3 text-body-sm text-text",
            position === "top" && "border-b border-border",
            position === "bottom" &&
              "fixed inset-x-0 bottom-16 z-40 border-t border-border lg:bottom-0",
          )}
        >
          <p className="min-w-0 flex-1">{message}</p>
          {(feedback || cta) && (
            <div className="flex items-center gap-3">
              {feedback}
              {cta && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={cta.onClick}
                  disabled={cta.disabled}
                >
                  {cta.label}
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
}
