"use client";

import * as React from "react";
import { ConsentDialog } from "@/components/ui/consent-dialog";

type SkipDialogStep2Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void | Promise<void>;
  isSubmitting?: boolean;
};

/** AC8 — "Plus tard" dialog for onboarding step-2. */
export function SkipDialog({ open, onOpenChange, onConfirm, isSubmitting }: SkipDialogStep2Props) {
  return (
    <ConsentDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Tu veux remettre ça à plus tard ?"
      description="Sans ton niveau scolaire, on ne peut pas adapter les recos à ta trajectoire ni te notifier du bon calendrier (Parcoursup ou Affelnet). Tu peux compléter à tout moment depuis ton profil — mais on t'enverra des recos plus génériques pour l'instant."
      dataMentioned={["Niveau scolaire", "Filière", "Spécialités (si applicable)"]}
      duration="Tu peux compléter à tout moment depuis ton profil"
      beneficiary="Toi — c'est ton parcours, tu décides"
      acceptLabel="Oui, plus tard"
      refuseLabel="Je continue"
      isAcceptDestructive={false}
      isSubmitting={isSubmitting}
      onAccept={onConfirm}
    />
  );
}
