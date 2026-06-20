"use client";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { StudentProfile } from "@/hooks/use-student-profile";

interface EditBulletinsSheetProps {
  open: boolean;
  profile: Pick<StudentProfile, "bulletins_status">;
  onClose: () => void;
  onSaved: () => void;
}

export function EditBulletinsSheet({
  open,
  onClose,
  onSaved: _onSaved,
}: EditBulletinsSheetProps) {
  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="bottom">
        <SheetHeader>
          <SheetTitle>Modifier les bulletins</SheetTitle>
        </SheetHeader>
        <div className="py-4 space-y-4">
          <p className="text-sm text-muted-foreground">
            Liste de vos bulletins actuels (BulletinRecapEditor / ManualBulletinForm Story 2.3/2.4).
          </p>
          <Button variant="outline" size="sm">
            Ajouter un trimestre
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
