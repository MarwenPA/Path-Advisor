"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/*
 * ConsentDialog — Couche 3 Path-Advisor composite (Story 1.14).
 *
 * Deferred follow-ups (tracked in deferred-work.md):
 *   - Audit-log POST of ConsentMeta — Story 1.13 + each consumer
 *   - axe-core automated a11y CI gate — cross-cutting Sprint 3+
 *   - motion-narrative is intentionally NOT used here — reserved for Epic 4 graph
 *
 * Implementation note: we deliberately re-compose Radix primitives instead of
 * using the shipped `<DialogContent>` wrapper from `./dialog.tsx`: that wrapper
 * injects an auto X close button which would be an ambiguous "close" action on
 * a consent capture (AC4). We keep `dialog.tsx` untouched and rebuild the
 * Portal → Overlay → Content stack here.
 */

export type ConsentMeta = {
  acceptedAt: string;
  contentHash: string;
};

export type ConsentDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  dataMentioned: string[];
  duration: string;
  beneficiary: string;
  acceptLabel?: string;
  refuseLabel?: string;
  isAcceptDestructive?: boolean;
  isSubmitting?: boolean;
  /**
   * Whether the accept action is currently blocked by a caller-side condition
   * (e.g. a required password input is empty). Distinct from `isSubmitting`
   * (which blocks both buttons during async work) — `isAcceptDisabled` only
   * blocks the accept button, leaving refuse available.
   *
   * Added in Story 1.12 for the deletion-confirmation flow where the dialog
   * embeds an inline password field via `bodySlot`.
   */
  isAcceptDisabled?: boolean;
  /**
   * Optional content rendered inside the dialog body, AFTER the bénéficiaire
   * line and BEFORE the footer. Use for inline secondary inputs that must
   * not appear as a separate dialog step (e.g. password re-auth for
   * destructive consent in Story 1.12 §AC1).
   *
   * The slot is rendered inside the same scroll container as the data list
   * so very tall inputs still scroll instead of pushing the footer below
   * the viewport.
   */
  bodySlot?: React.ReactNode;
  onAccept: (meta: ConsentMeta) => void | Promise<void>;
  onRefuse?: () => void;
};

// Hash inputs match what the user SEES, including resolved labels and the
// destructive intent flag — two visually different consents must produce
// different audit hashes (story 1.14 review decision: 8-field canonical JSON).
async function computeContentHash(input: {
  acceptLabel: string;
  beneficiary: string;
  dataMentioned: string[];
  description: string;
  duration: string;
  isAcceptDestructive: boolean;
  refuseLabel: string;
  title: string;
}): Promise<string> {
  const canonical = JSON.stringify({
    acceptLabel: input.acceptLabel,
    beneficiary: input.beneficiary,
    dataMentioned: input.dataMentioned, // caller order preserved on purpose
    description: input.description,
    duration: input.duration,
    isAcceptDestructive: input.isAcceptDestructive,
    refuseLabel: input.refuseLabel,
    title: input.title,
  });
  // Story 2.1 Pass 1 M8 — `crypto.subtle` is undefined in insecure
  // contexts (dev tunnels without HTTPS, certain embedded WebViews, very
  // old browsers). The previous implementation threw, the handler caught
  // and never invoked `onAccept`, and the dialog hung silently. Feature-
  // detect and fall back to a tagged sentinel `"crypto-unavailable:<hex>"`
  // where the hex segment is a non-crypto djb2 hash of the canonical JSON.
  // The audit row keeps something queryable; the prefix tells the DPO
  // playbook the hash is not collision-resistant for this specific row.
  if (!globalThis.crypto?.subtle?.digest) {
    let h = 5381;
    for (let i = 0; i < canonical.length; i += 1) {
      h = ((h << 5) + h + canonical.charCodeAt(i)) | 0;
    }
    return `crypto-unavailable:${(h >>> 0).toString(16).padStart(8, "0")}`;
  }
  const bytes = new TextEncoder().encode(canonical);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function ConsentDialog({
  open,
  onOpenChange,
  title,
  description,
  dataMentioned,
  duration,
  beneficiary,
  acceptLabel,
  refuseLabel,
  isAcceptDestructive = false,
  isSubmitting = false,
  isAcceptDisabled = false,
  bodySlot,
  onAccept,
  onRefuse,
}: ConsentDialogProps) {
  // Empty-string labels must fall back to the French defaults — default-parameter
  // syntax only applies on `undefined`, so we resolve explicitly here.
  const resolvedAcceptLabel = acceptLabel || "Accepter";
  const resolvedRefuseLabel = refuseLabel || "Refuser";

  const refuseButtonRef = React.useRef<HTMLButtonElement>(null);
  const contentRef = React.useRef<HTMLDivElement>(null);
  // Re-entry guard: blocks rapid Accept→Refuse races and double-click bursts
  // even when the consumer hasn't flipped `isSubmitting` yet.
  const isPendingRef = React.useRef(false);

  const handleOpenChange = (next: boolean) => {
    if (next === false && isSubmitting) {
      // Should never reach here — onEscapeKeyDown / onPointerDownOutside block
      // the close while submitting. Defensive: drop the call silently.
      return;
    }
    if (!next) {
      onRefuse?.();
    }
    onOpenChange(next);
  };

  const handleRefuse = () => {
    handleOpenChange(false);
  };

  const handleAccept = async () => {
    if (isPendingRef.current) return;
    isPendingRef.current = true;
    const acceptedAt = new Date().toISOString();
    try {
      const contentHash = await computeContentHash({
        acceptLabel: resolvedAcceptLabel,
        beneficiary,
        dataMentioned,
        description,
        duration,
        isAcceptDestructive,
        refuseLabel: resolvedRefuseLabel,
        title,
      });
      await onAccept({ acceptedAt, contentHash });
    } catch (error) {
      // Surface to consumer telemetry via console; do NOT re-throw — that
      // turns into an unhandled rejection on the click microtask. Consumers
      // that need structured error handling should try/catch inside their
      // own `onAccept` implementation.
      console.error("[ConsentDialog] onAccept failed:", error);
    } finally {
      isPendingRef.current = false;
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogPortal>
        <DialogOverlay />
        <DialogPrimitive.Content
          ref={contentRef}
          aria-busy={isSubmitting}
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            // Fallback to Content focus if the button ref isn't attached yet
            // (Strict Mode double-mount).
            (refuseButtonRef.current ?? contentRef.current)?.focus();
          }}
          onEscapeKeyDown={(event) => {
            if (isSubmitting) event.preventDefault();
          }}
          onPointerDownOutside={(event) => {
            if (isSubmitting) event.preventDefault();
          }}
          className={cn(
            "fixed bottom-0 left-0 right-0 z-50 flex max-h-[90vh] w-full flex-col gap-4 overflow-hidden rounded-t-lg border bg-background px-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-6 shadow-lg duration-quick",
            "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
            "sm:bottom-auto sm:left-1/2 sm:right-auto sm:top-1/2 sm:max-h-[85vh] sm:max-w-lg sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-lg sm:pb-6",
          )}
          // Content needs a tabIndex to be a focus fallback target.
          tabIndex={-1}
        >
          <DialogHeader>
            <DialogTitle className="text-h2 md:text-h2-desktop">{title}</DialogTitle>
            <DialogDescription className="text-body">{description}</DialogDescription>
          </DialogHeader>

          <section className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
            <div className="flex flex-col gap-1">
              <span className="text-body-sm font-medium text-text-muted">Données concernées</span>
              <ul className="list-disc pl-5 text-body text-text">
                {dataMentioned.map((item, index) => (
                  <li key={`${index}-${item}`}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-body-sm font-medium text-text-muted">Durée</span>
              <p className="text-body text-text">{duration}</p>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-body-sm font-medium text-text-muted">Bénéficiaire</span>
              <p className="text-body text-text">{beneficiary}</p>
            </div>
            {bodySlot ? <div className="mt-2">{bodySlot}</div> : null}
          </section>

          {/* Screen-reader announces submit state; spinner stays aria-hidden. */}
          <span role="status" aria-live="polite" className="sr-only">
            {isSubmitting ? "Envoi en cours…" : ""}
          </span>

          <DialogFooter className="sticky bottom-0 -mx-6 -mb-6 bg-background px-6 pb-6 pt-2 sm:static sm:m-0 sm:bg-transparent sm:p-0">
            <Button
              ref={refuseButtonRef}
              variant="outline"
              onClick={handleRefuse}
              disabled={isSubmitting}
            >
              {resolvedRefuseLabel}
            </Button>
            <Button
              variant={isAcceptDestructive ? "destructive" : "default"}
              onClick={() => {
                void handleAccept();
              }}
              disabled={isSubmitting || isAcceptDisabled}
            >
              {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden /> : null}
              {resolvedAcceptLabel}
            </Button>
          </DialogFooter>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}

export default ConsentDialog;
