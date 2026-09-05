"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { StudentProfile } from "@/hooks/use-student-profile";

interface EditBulletinsSheetProps {
  open: boolean;
  profile: Pick<StudentProfile, "bulletins_status">;
  onClose: () => void;
  onSaved: () => void;
}

const STATUS_LABELS: Record<StudentProfile["bulletins_status"], string> = {
  pending: "Tu n'as pas encore ajouté de bulletin.",
  postponed: "Tu as choisi d'ajouter tes bulletins plus tard.",
  partial: "Certains de tes bulletins sont encore en cours de vérification.",
  completed: "Tes bulletins sont à jour.",
};

/**
 * Code-review fix (2026-09) — "lie l'onboarding au profil": this used to be
 * a dead stub (`<Button>Ajouter un trimestre</Button>` with no `onClick` at
 * all — the exact bug reported live). The real upload/OCR flow
 * (`BulletinRecapEditor`/`ManualBulletinForm`, an xstate machine with file
 * upload, OCR polling, and a manual-entry fallback) is `/onboarding/step-3`
 * — deliberately NOT re-embedded inline here: duplicating that state
 * machine into a `Sheet` would mean two divergent code paths for the exact
 * same feature. Instead this sheet shows the current status and links
 * straight to the real flow, closing itself first — same route, same data,
 * one path.
 */
export function EditBulletinsSheet({
  open,
  profile,
  onClose,
  onSaved: _onSaved,
}: EditBulletinsSheetProps) {
  const router = useRouter();

  function handleGoToBulletins() {
    onClose();
    router.push("/onboarding/step-3");
  }

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="bottom">
        <SheetHeader>
          <SheetTitle>Bulletins</SheetTitle>
        </SheetHeader>
        <div className="space-y-4 py-4">
          <p className="text-sm text-muted-foreground">{STATUS_LABELS[profile.bulletins_status]}</p>
        </div>
        <SheetFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Fermer
          </Button>
          <Button onClick={handleGoToBulletins}>Gérer mes bulletins</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
