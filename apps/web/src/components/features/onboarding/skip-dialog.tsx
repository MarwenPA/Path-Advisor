"use client";

import * as React from "react";

import { ConsentDialog } from "@/components/ui/consent-dialog";

/**
 * `<SkipDialog>` — Story 2.1 §AC7. Compose `ConsentDialog` (Story 1.14)
 * with the literal copy the spec dictates. Surfaced from the header
 * "Plus tard" button. Confirmation persists the current draft
 * server-side as `step1_skipped` (or `partial_skipped` if some
 * sub-step had data) and redirects to `/onboarding/step-2`.
 *
 * `onConfirm` is async so the orchestrator can await the PATCH
 * before navigating — failures keep the dialog open via
 * `ConsentDialog`'s built-in submitting state.
 */

export type SkipDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void | Promise<void>;
  /** Surfaced as the dialog's submitting state — disables both CTAs
   *  and prevents close while the PATCH is in flight. */
  isSubmitting?: boolean;
};

export function SkipDialog({ open, onOpenChange, onConfirm, isSubmitting }: SkipDialogProps) {
  return (
    <ConsentDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Tu veux remettre ça à plus tard ?"
      description={
        "Pas de souci. Tu pourras déclarer tes passions, valeurs et centres d'intérêt à tout moment depuis ton profil. Tes recos seront un peu plus génériques pour l'instant, mais elles s'affineront dès que tu reviendras compléter."
      }
      dataMentioned={[
        "Tes passions et valeurs sont utilisées pour adapter tes recos métiers",
      ]}
      duration="Tu peux compléter à tout moment depuis ton profil"
      beneficiary="Toi — ce sont tes données, tu décides"
      acceptLabel="Oui, plus tard"
      refuseLabel="Je continue"
      isAcceptDestructive={false}
      isSubmitting={isSubmitting}
      onAccept={onConfirm}
    />
  );
}
