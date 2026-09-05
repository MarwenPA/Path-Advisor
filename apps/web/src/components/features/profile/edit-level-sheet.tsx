"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Branche3eme } from "@/components/features/onboarding/branche-3eme";
import { BrancheLycee } from "@/components/features/onboarding/branche-lycee";
import { BranchePostbac } from "@/components/features/onboarding/branche-postbac";
import { NiveauPicker } from "@/components/features/onboarding/niveau-picker";
import {
  fetchOnboardingStep2Snapshot,
  patchOnboardingStep2,
  type OnboardingStep2Snapshot,
} from "@/lib/api/onboarding";
import { readCsrfCookie } from "@/lib/api/client";
import {
  REF_VERSION,
  type FiliereId,
  type NiveauId,
  type PostbacFormationId,
  type PostbacYearId,
  type SousFiliereId,
  type Track3emeId,
} from "@/lib/onboarding/levels";
import type { StudentProfile } from "@/hooks/use-student-profile";

interface EditLevelSheetProps {
  open: boolean;
  profile: Pick<StudentProfile, "level" | "filiere" | "specialites" | "sous_filiere_techno">;
  onClose: () => void;
  onSaved: () => void;
}

/**
 * Code-review fix (2026-09) — "lie l'onboarding au profil": this used to be
 * a read-only placeholder ("Story 2.2 LevelForm PATCH wired here in
 * production") whose "Sauvegarder" button didn't call anything. Now reuses
 * `/onboarding/step-2`'s own controlled branch components
 * (`NiveauPicker`/`Branche3eme`/`BrancheLycee`/`BranchePostbac`) and its
 * PATCH endpoint (`patchOnboardingStep2`, `commit: true`) — same row,
 * same validation, no separate data path.
 *
 * `StudentProfile` (the `/profile` summary) doesn't carry
 * `intended_track`/`postbac_year`/`postbac_formation_type` — only the full
 * step-2 snapshot does — so this sheet fetches its own snapshot on open
 * rather than trusting the summary prop for the branch-specific fields.
 */
export function EditLevelSheet({ open, onClose, onSaved }: EditLevelSheetProps) {
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingSnapshot, setIsLoadingSnapshot] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<OnboardingStep2Snapshot | null>(null);

  useEffect(() => {
    // Code-review fix: no synchronous `setState` at the top of the effect
    // body (react-hooks/set-state-in-effect) — `isLoadingSnapshot` starts
    // `true` from its initializer and is only ever flipped `false` from an
    // async callback below, never reset back to `true` on a later re-open.
    // A second open of the same sheet instance re-fetches silently and
    // swaps the snapshot in once ready, rather than flashing "Chargement…"
    // again — acceptable for a sheet that's opened, edited, and closed.
    if (!open) return;
    let cancelled = false;
    fetchOnboardingStep2Snapshot()
      .then((s) => {
        if (!cancelled) setSnapshot(s);
      })
      .catch(() => {
        if (!cancelled) setError("Impossible de charger ton niveau. Réessaie plus tard.");
      })
      .finally(() => {
        if (!cancelled) setIsLoadingSnapshot(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const level = (snapshot?.level ?? null) as NiveauId | null;
  const branch = level === "college_3eme" ? "college" : level === "postbac" ? "postbac" : "lycee";

  function updateSnapshot(partial: Partial<OnboardingStep2Snapshot>) {
    setSnapshot((prev) => (prev ? { ...prev, ...partial } : prev));
  }

  async function handleSave() {
    if (!snapshot) return;
    setIsSaving(true);
    setError(null);
    try {
      const csrfToken = readCsrfCookie() ?? "";
      const updated = await patchOnboardingStep2(
        {
          commit: true,
          level: snapshot.level,
          filiere: snapshot.filiere,
          sous_filiere_techno: snapshot.sous_filiere_techno,
          specialites: snapshot.specialites,
          intended_track: snapshot.intended_track,
          postbac_year: snapshot.postbac_year,
          postbac_formation_type: snapshot.postbac_formation_type,
          level_ref_version: REF_VERSION,
        },
        csrfToken,
      );
      setSnapshot(updated);
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
      <SheetContent side="right" className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Modifier le niveau scolaire</SheetTitle>
        </SheetHeader>
        <div className="space-y-4 py-4">
          {isLoadingSnapshot || !snapshot ? (
            <p className="text-sm text-muted-foreground">Chargement…</p>
          ) : (
            <>
              <NiveauPicker value={level} onChange={(next) => updateSnapshot({ level: next })} />
              {/* Code-review note: the snapshot's fields come back from the
                  same PATCH endpoint these branch components write to, typed
                  loosely (`string | null`) at the API-client boundary — same
                  trust boundary `useOnboardingStep2`'s own `snapshotToDraft`
                  conversion relies on, not re-validated client-side here. */}
              {branch === "college" && (
                <Branche3eme
                  value={snapshot.intended_track as Track3emeId | null}
                  onChange={(v) => updateSnapshot({ intended_track: v })}
                />
              )}
              {branch === "lycee" && level && (
                <BrancheLycee
                  level={level}
                  filiere={snapshot.filiere as FiliereId | null}
                  sousFiliere={snapshot.sous_filiere_techno as SousFiliereId | null}
                  specialites={[...snapshot.specialites]}
                  onFiliereChange={(v) => updateSnapshot({ filiere: v })}
                  onSousFiliereChange={(v) => updateSnapshot({ sous_filiere_techno: v })}
                  onToggleSpecialite={(spec) =>
                    setSnapshot((prev) => {
                      if (!prev) return prev;
                      const has = prev.specialites.includes(spec);
                      return {
                        ...prev,
                        specialites: has
                          ? prev.specialites.filter((s) => s !== spec)
                          : [...prev.specialites, spec],
                      };
                    })
                  }
                />
              )}
              {branch === "postbac" && (
                <BranchePostbac
                  year={snapshot.postbac_year as PostbacYearId | null}
                  formationType={snapshot.postbac_formation_type as PostbacFormationId | null}
                  onYearChange={(v) => updateSnapshot({ postbac_year: v })}
                  onFormationChange={(v) => updateSnapshot({ postbac_formation_type: v })}
                />
              )}
              <p className="mt-4 text-xs text-muted-foreground">
                Changer de filière déclenchera un recalcul des recos.
              </p>
            </>
          )}
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
          <Button onClick={handleSave} disabled={isSaving || isLoadingSnapshot || !snapshot}>
            {isSaving ? "Enregistrement…" : "Sauvegarder"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
