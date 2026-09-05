"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { InteretsFreeForm } from "@/components/features/onboarding/interets-free-form";
import { PassionsPicker } from "@/components/features/onboarding/passions-picker";
import { ValeursPicker } from "@/components/features/onboarding/valeurs-picker";
import { patchOnboardingStep1, type OnboardingInterets } from "@/lib/api/onboarding";
import { readCsrfCookie } from "@/lib/api/client";
import type { StudentProfile } from "@/hooks/use-student-profile";

interface EditPassionsSheetProps {
  open: boolean;
  profile: Pick<StudentProfile, "passions" | "valeurs" | "interets">;
  onClose: () => void;
  onSaved: () => void;
}

/**
 * Code-review fix (2026-09) — "lie l'onboarding au profil" : this used to be
 * a placeholder (a paragraph of text saying the real pickers "sont branchés
 * en prod") backed by a bare `fetch()` that hit the wrong host. Now reuses
 * the SAME controlled picker components step-1 of `/onboarding` uses
 * (`PassionsPicker`/`ValeursPicker`/`InteretsFreeForm`) and the SAME typed
 * PATCH endpoint (`patchOnboardingStep1`, one sub-step at a time per its
 * discriminated-union contract) — editing here and completing onboarding
 * write to the exact same `onboarding_step1` row, no separate/duplicated
 * data path.
 */
export function EditPassionsSheet({ open, profile, onClose, onSaved }: EditPassionsSheetProps) {
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passions, setPassions] = useState<readonly string[]>(profile.passions ?? []);
  const [valeurs, setValeurs] = useState<readonly string[]>(profile.valeurs ?? []);
  const [interets, setInterets] = useState<OnboardingInterets>(
    profile.interets
      ? { "1": null, "2": null, "3": null, ...(profile.interets as Partial<OnboardingInterets>) }
      : { "1": null, "2": null, "3": null },
  );

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    try {
      const csrfToken = readCsrfCookie() ?? "";
      // One PATCH per sub-step — the endpoint's discriminated-union payload
      // (`step: "passions" | "valeurs" | "interets"`) rejects a mixed body,
      // same contract `useOnboardingStep1` already follows.
      await patchOnboardingStep1({ step: "passions", passions }, csrfToken);
      await patchOnboardingStep1({ step: "valeurs", valeurs }, csrfToken);
      await patchOnboardingStep1({ step: "interets", interets }, csrfToken);
      await queryClient.invalidateQueries({ queryKey: ["student-profile"] });
      onSaved();
    } catch {
      setError("Une erreur est survenue. Vérifie ta connexion et réessaie.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="bottom" className="max-h-[90vh] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Modifier passions, intérêts et valeurs</SheetTitle>
        </SheetHeader>
        <div className="space-y-8 py-4">
          <section aria-labelledby="edit-passions-heading">
            <h3 id="edit-passions-heading" className="mb-2 text-sm font-semibold">
              Passions
            </h3>
            <PassionsPicker selected={passions} onChange={setPassions} />
          </section>
          <section aria-labelledby="edit-valeurs-heading">
            <h3 id="edit-valeurs-heading" className="mb-2 text-sm font-semibold">
              Valeurs
            </h3>
            <ValeursPicker selected={valeurs} onChange={setValeurs} />
          </section>
          <section aria-labelledby="edit-interets-heading">
            <h3 id="edit-interets-heading" className="mb-2 text-sm font-semibold">
              Centres d&apos;intérêt
            </h3>
            <InteretsFreeForm value={interets} onChange={setInterets} />
          </section>
          {error && (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          )}
        </div>
        <SheetFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Annuler
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Enregistrement…" : "Sauvegarder"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
