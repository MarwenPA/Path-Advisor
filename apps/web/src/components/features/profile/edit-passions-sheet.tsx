"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { StudentProfile } from "@/hooks/use-student-profile";

interface EditPassionsSheetProps {
  open: boolean;
  profile: Pick<StudentProfile, "passions" | "valeurs" | "interets">;
  onClose: () => void;
  onSaved: () => void;
}

export function EditPassionsSheet({
  open,
  profile,
  onClose,
  onSaved,
}: EditPassionsSheetProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [draft, setDraft] = useState({
    passions: profile.passions ?? [],
    valeurs: profile.valeurs ?? [],
    interets: profile.interets ?? {},
  });

  async function handleSave() {
    setIsSaving(true);
    try {
      await fetch("/api/v1/students/me/onboarding/passions", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      onSaved();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="bottom">
        <SheetHeader>
          <SheetTitle>Modifier passions, intérêts et valeurs</SheetTitle>
        </SheetHeader>
        <div className="py-4">
          {/* Story 2.1 PassionsPicker / ValeursPicker / InteretsFreeForm are wired here in production */}
          <p className="text-sm text-muted-foreground">
            Édition des passions, valeurs et intérêts (composants Story 2.1).
          </p>
        </div>
        <SheetFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Annuler
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            Sauvegarder
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
