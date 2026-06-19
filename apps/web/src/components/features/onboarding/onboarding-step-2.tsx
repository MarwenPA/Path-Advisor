"use client";

/**
 * `<OnboardingStep2>` — Story 2.2 orchestrator.
 *
 * Manages the editing ↔ recap state machine. Delegates branch rendering
 * to `<Branche3eme>`, `<BrancheLycee>`, `<BranchePostbac>`.
 * Recap is rendered by `<RecapCard>`.
 *
 * AC6 — "Continuer" on edit view → recap; "Continuer vers les bulletins"
 *        on recap → commits + redirects to /onboarding/step-3.
 * AC7 — localStorage draft + server snapshot merged on mount.
 * AC8 — "Plus tard" → <SkipDialog> → skip PATCH + redirect step-3.
 * AC11 — already completed → redirect step-3.
 */

import * as React from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProgressDots } from "./progress-dots";
import { NiveauPicker } from "./niveau-picker";
import { Branche3eme } from "./branche-3eme";
import { BrancheLycee } from "./branche-lycee";
import { BranchePostbac } from "./branche-postbac";
import { RecapCard } from "./recap-card";
import { SkipDialog } from "./skip-dialog-step2";
import { useOnboardingStep2 } from "@/hooks/use-onboarding-step-2";
import type { NiveauId } from "@/lib/onboarding/levels";

type ViewState = "editing" | "recap";

export function OnboardingStep2() {
  const router = useRouter();
  const { data: session } = useSession();
  const userId = session?.user?.id;

  const {
    snapshot,
    draft,
    isLoading,
    isSaving,
    setLevel,
    setFiliere,
    setSousFiliere,
    toggleSpecialite,
    setIntendedTrack,
    setPostbacYear,
    setPostbacFormationType,
    commitLevel,
    skipStep,
    isDraftComplete,
  } = useOnboardingStep2({ userId });

  const [view, setView] = React.useState<ViewState>("editing");
  const [skipOpen, setSkipOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // AC10 aria-live announcer
  const announcerRef = React.useRef<HTMLDivElement>(null!);

  // AC11 — already completed → redirect
  React.useEffect(() => {
    if (snapshot.onboarding_step2_status === "completed") {
      router.replace("/onboarding/step-3");
    }
  }, [snapshot.onboarding_step2_status, router]);

  const handleContinueFromEditing = () => {
    if (!isDraftComplete) return;
    setView("recap");
    // AC10 — announce transition
    if (announcerRef.current) {
      announcerRef.current.textContent =
        "Récap de tes informations scolaires. Vérifie avant de continuer.";
    }
  };

  const handleCommit = async () => {
    setIsSubmitting(true);
    try {
      await commitLevel();
      router.push("/onboarding/step-3");
    } catch {
      // Stay on recap — network error toast handled globally
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkipConfirm = async () => {
    await skipStep();
    router.push("/onboarding/step-3");
  };

  const getLevelBranch = () => {
    if (!draft.level) return null;
    if (draft.level === "college_3eme") return "college";
    if (draft.level === "postbac") return "postbac";
    return "lycee";
  };

  const branch = getLevelBranch();

  const continueHelper = (() => {
    if (!draft.level) return "Choisis ton niveau pour continuer.";
    if (!isDraftComplete) {
      if (branch === "lycee" && !draft.filiere) return "Choisis ta filière pour continuer.";
      if (branch === "lycee" && draft.filiere === "techno" && !draft.sous_filiere_techno)
        return "Précise ta sous-filière techno.";
      if (branch === "lycee" && draft.specialites.length === 0)
        return "Sélectionne tes spécialités pour continuer.";
      if (branch === "postbac" && !draft.postbac_year) return "Indique ton niveau actuel.";
      if (branch === "postbac" && !draft.postbac_formation_type)
        return "Indique ta situation de formation.";
    }
    return null;
  })();

  if (isLoading) {
    return (
      <main className="mx-auto flex w-full max-w-[600px] flex-1 flex-col gap-6 px-4 py-12">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
      </main>
    );
  }

  return (
    <>
      {/* AC10 — SR-only live region for branch transition announcements */}
      <div
        ref={announcerRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />

      {/* Skip link NFR-A1 */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-bg focus:px-4 focus:py-2 focus:text-brand"
      >
        Aller au contenu principal
      </a>

      {/* Header sticky */}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-bg px-4 py-3">
        <button
          type="button"
          onClick={() => router.push("/onboarding/step-1")}
          aria-label="Retour à l'étape précédente"
          className="flex items-center gap-1 text-text-muted hover:text-text"
        >
          <span aria-hidden>‹</span>
        </button>

        <ProgressDots total={3} current={2} />

        <button
          type="button"
          onClick={() => setSkipOpen(true)}
          className="text-body-sm text-text-muted hover:text-text"
        >
          Plus tard
        </button>
      </header>

      <main
        id="main-content"
        className="mx-auto flex w-full max-w-[600px] flex-1 flex-col gap-8 px-4 py-8 pb-32"
      >
        {view === "recap" ? (
          <RecapCard
            draft={draft}
            onModify={() => {
              setView("editing");
              if (announcerRef.current) {
                announcerRef.current.textContent = "Modification de tes informations scolaires.";
              }
            }}
          />
        ) : (
          <>
            <section aria-labelledby="niveau-heading" className="flex flex-col gap-4">
              <div>
                <h2 id="niveau-heading" className="text-h2 font-semibold text-text">
                  Où tu en es, scolairement ?
                </h2>
                <p className="mt-1 text-body text-text-muted">
                  Pour qu&apos;on t&apos;envoie les bonnes infos au bon moment.
                </p>
              </div>

              <NiveauPicker
                value={draft.level}
                onChange={(level) => setLevel(level as NiveauId)}
                announcerRef={announcerRef}
              />
            </section>

            {/* Branch — rendered inline, no page change */}
            {branch === "college" && (
              <Branche3eme
                value={draft.intended_track}
                onChange={setIntendedTrack}
              />
            )}

            {branch === "lycee" && draft.level && (
              <BrancheLycee
                level={draft.level}
                filiere={draft.filiere}
                sousFiliere={draft.sous_filiere_techno}
                specialites={draft.specialites}
                onFiliereChange={setFiliere}
                onSousFiliereChange={setSousFiliere}
                onToggleSpecialite={toggleSpecialite}
                announcerRef={announcerRef}
              />
            )}

            {branch === "postbac" && (
              <BranchePostbac
                year={draft.postbac_year}
                formationType={draft.postbac_formation_type}
                onYearChange={setPostbacYear}
                onFormationChange={setPostbacFormationType}
              />
            )}
          </>
        )}
      </main>

      {/* Footer sticky */}
      <footer className="fixed bottom-0 left-0 right-0 border-t border-border bg-bg px-4 py-4">
        <div className="mx-auto flex max-w-[600px] flex-col items-end gap-1">
          {view === "editing" ? (
            <>
              <Button
                size="lg"
                className="w-full md:w-auto"
                disabled={!isDraftComplete || isSaving}
                onClick={handleContinueFromEditing}
              >
                Continuer
              </Button>
              {continueHelper && (
                <p className="text-body-sm text-text-muted">{continueHelper}</p>
              )}
            </>
          ) : (
            <Button
              size="lg"
              className="w-full md:w-auto"
              disabled={isSubmitting}
              onClick={handleCommit}
            >
              {isSubmitting ? "Enregistrement…" : "Continuer vers les bulletins"}
            </Button>
          )}
        </div>
      </footer>

      <SkipDialog
        open={skipOpen}
        onOpenChange={setSkipOpen}
        onConfirm={handleSkipConfirm}
        isSubmitting={isSaving}
      />
    </>
  );
}
