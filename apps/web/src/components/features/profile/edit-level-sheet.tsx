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

const LEVEL_LABELS: Record<string, string> = {
  lycee_terminale: "Terminale",
  lycee_premiere: "Première",
  lycee_2nde: "Seconde",
  college_3eme: "3ème",
  college_4eme: "4ème",
  postbac: "Post-bac",
};

interface EditLevelSheetProps {
  open: boolean;
  profile: Pick<StudentProfile, "level" | "filiere" | "specialites" | "sous_filiere_techno">;
  onClose: () => void;
  onSaved: () => void;
}

export function EditLevelSheet({
  open,
  profile,
  onClose,
  onSaved: _onSaved,
}: EditLevelSheetProps) {
  const [isSaving, setIsSaving] = useState(false);
  const levelLabel = profile.level ? (LEVEL_LABELS[profile.level] ?? profile.level) : "—";

  async function handleSave() {
    setIsSaving(true);
    try {
      // Story 2.2 LevelForm PATCH wired here in production (major change triggers ConsentDialog)
      onClose();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="right">
        <SheetHeader>
          <SheetTitle>Modifier le niveau scolaire</SheetTitle>
        </SheetHeader>
        <div className="py-4 space-y-2">
          <p className="text-sm font-medium">{levelLabel}</p>
          {profile.filiere && (
            <p className="text-sm text-muted-foreground capitalize">{profile.filiere}</p>
          )}
          {!!profile.specialites?.length && (
            <p className="text-sm text-muted-foreground">
              {profile.specialites.join(" · ")}
            </p>
          )}
          <p className="text-xs text-muted-foreground mt-4">
            Changer de filière déclenchera une confirmation et un recalcul des recos.
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
