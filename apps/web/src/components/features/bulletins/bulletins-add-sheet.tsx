"use client";

import { Camera, PenLine } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

interface BulletinsAddSheetProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function BulletinsAddSheet({
  open,
  onClose,
  onSuccess,
}: BulletinsAddSheetProps) {
  if (!open) return null;

  return (
    <Sheet open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <SheetContent
        side="bottom"
        aria-modal="true"
        className="rounded-t-2xl px-6 pb-8 pt-4 sm:side-right"
      >
        <SheetHeader className="mb-6">
          <SheetTitle>Ajoute tes bulletins</SheetTitle>
          <p className="text-sm text-muted-foreground">
            En moins d'une minute, tes stats deviennent personnalisées.
          </p>
        </SheetHeader>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button
            variant="outline"
            className="flex-1 gap-2"
            onClick={() => {
              // Opens FilePickerSheet (Story 2.3) in nested context — wired by parent
              onSuccess();
            }}
          >
            <Camera size={18} aria-hidden="true" />
            Scanner / importer mes bulletins
          </Button>

          <Button
            variant="secondary"
            className="flex-1 gap-2"
            onClick={() => {
              // Opens MatiereInputRow mini-form (Story 2.4) in nested context
              onSuccess();
            }}
          >
            <PenLine size={18} aria-hidden="true" />
            Saisir à la main
          </Button>
        </div>

        <Button
          variant="ghost"
          className="mt-4 w-full text-muted-foreground"
          onClick={onClose}
        >
          Annuler
        </Button>
      </SheetContent>
    </Sheet>
  );
}
