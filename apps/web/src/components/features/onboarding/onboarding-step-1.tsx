"use client";

import * as React from "react";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useOnboardingStep1 } from "@/hooks/use-onboarding-step-1";
import {
  getOnboardingCopy,
  type SchoolLevel,
} from "@/lib/onboarding/level-adapter";
import {
  MIN_PASSIONS,
  MIN_VALEURS,
} from "@/lib/onboarding/referentials";
import type { OnboardingInterets } from "@/lib/api/onboarding";
import { cn } from "@/lib/utils";

import { InteretsFreeForm } from "./interets-free-form";
import { PassionsPicker } from "./passions-picker";
import { ProgressDots } from "./progress-dots";
import { SkipDialog } from "./skip-dialog";
import { ValeursPicker } from "./valeurs-picker";

/**
 * `<OnboardingStep1>` — Story 2.1 §AC1. Orchestrates the three sub-steps
 * (1A Passions → 1B Valeurs → 1C Intérêts) on `/onboarding/step-1`.
 *
 * State machine:
 *   - `substep` (1 | 2 | 3) — local state, initialised from the server
 *     snapshot so a user returning mid-flight resumes on the last
 *     in-flight sub-step (AC6 — silent reprise).
 *   - selections / intérêts text — local drafts kept in sync with the
 *     server snapshot via the hook's localStorage layer.
 *
 * Continue/Terminer button:
 *   - 1A : disabled until selectedPassions ≥ MIN_PASSIONS (3).
 *   - 1B : disabled until selectedValeurs ≥ MIN_VALEURS (3).
 *   - 1C : ALWAYS enabled (all fields optional per AC4).
 *
 * Skip dialog : surfaced from the header "Plus tard" button on every
 * sub-step. Confirming PATCHes `step="skip"` and routes to step-2.
 *
 * The component does NOT crash on PATCH failure — the local draft is
 * preserved by the hook so the user can keep moving; we surface a
 * compact info banner under the Continue button.
 */

const SCHOOL_LEVEL: SchoolLevel = "lycee";

export function OnboardingStep1() {
  const router = useRouter();
  const {
    snapshot,
    isLoading,
    submit,
    isSubmitting,
    submitError,
  } = useOnboardingStep1();

  const copy = React.useMemo(() => getOnboardingCopy(SCHOOL_LEVEL), []);

  // Local drafts — start from snapshot, kept in sync via effect when the
  // snapshot changes (initial load or after a PATCH).
  const [passionsDraft, setPassionsDraft] = React.useState<readonly string[]>(snapshot.passions);
  const [valeursDraft, setValeursDraft] = React.useState<readonly string[]>(snapshot.valeurs);
  const [interetsDraft, setInteretsDraft] = React.useState<OnboardingInterets>(snapshot.interets);

  // Substep state — derived from snapshot status on first render, then
  // owned by local state. `prevSnapshotStatus` tracks the last value we
  // applied so a manual back-navigation via the dots isn't immediately
  // reverted by an incoming snapshot.
  const initialSubstep = React.useMemo<1 | 2 | 3>(() => {
    if (snapshot.passions.length === 0) return 1;
    if (snapshot.valeurs.length === 0) return 2;
    return 3;
  }, [snapshot.passions.length, snapshot.valeurs.length]);
  const [substep, setSubstep] = React.useState<1 | 2 | 3>(initialSubstep);

  // Sync local drafts when the snapshot changes (post-PATCH or post-fetch).
  const lastSyncedRef = React.useRef<string>("");
  React.useEffect(() => {
    const fingerprint = JSON.stringify({
      p: snapshot.passions,
      v: snapshot.valeurs,
      i: snapshot.interets,
    });
    if (fingerprint === lastSyncedRef.current) return;
    lastSyncedRef.current = fingerprint;
    setPassionsDraft(snapshot.passions);
    setValeursDraft(snapshot.valeurs);
    setInteretsDraft(snapshot.interets);
  }, [snapshot]);

  // AC10 — if the server says step-1 is already completed (e.g. user
  // navigates back here after the fact), redirect to step-2 instantly.
  React.useEffect(() => {
    if (snapshot.onboarding_step1_status === "completed") {
      router.replace("/onboarding/step-2");
    }
  }, [snapshot.onboarding_step1_status, router]);

  // SR announcer for substep transitions (AC6 — "Étape 2 sur 3 : valeurs").
  const [srMessage, setSrMessage] = React.useState("");
  const setSubstepWithAnnounce = (next: 1 | 2 | 3, label: string) => {
    setSubstep(next);
    setSrMessage(`Étape ${next} sur 3 : ${label}`);
  };

  // Skip dialog ----------------------------------------------------------

  const [skipOpen, setSkipOpen] = React.useState(false);
  const handleSkipConfirm = React.useCallback(async () => {
    try {
      await submit({ step: "skip" });
    } finally {
      router.push("/onboarding/step-2");
    }
  }, [router, submit]);

  // Continue handlers ----------------------------------------------------

  const handleContinuePassions = async () => {
    if (passionsDraft.length < MIN_PASSIONS) return;
    try {
      await submit({ step: "passions", passions: passionsDraft });
    } catch {
      // Hook keeps the draft in localStorage; UX > strict sync (AC5).
    }
    setSubstepWithAnnounce(2, "valeurs");
  };

  const handleContinueValeurs = async () => {
    if (valeursDraft.length < MIN_VALEURS) return;
    try {
      await submit({ step: "valeurs", valeurs: valeursDraft });
    } catch {
      // localStorage draft preserves the selection.
    }
    setSubstepWithAnnounce(3, "centres d'intérêt");
  };

  const handleFinishInterets = async () => {
    try {
      await submit({ step: "interets", interets: interetsDraft });
    } catch {
      // localStorage preserves the draft; user can retry from /profile.
    }
    router.push("/onboarding/step-2");
  };

  // Render --------------------------------------------------------------

  if (isLoading) {
    return (
      <main className="mx-auto flex w-full max-w-[600px] flex-col gap-6 px-4 py-6 sm:px-6">
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 10 }).map((_, idx) => (
            <Skeleton key={idx} className="h-10 w-24 rounded-full" />
          ))}
        </div>
      </main>
    );
  }

  const canContinue =
    (substep === 1 && passionsDraft.length >= MIN_PASSIONS) ||
    (substep === 2 && valeursDraft.length >= MIN_VALEURS) ||
    substep === 3;

  const continueLabel = substep === 3 ? "Terminer" : "Continuer";
  const continueHandler =
    substep === 1
      ? handleContinuePassions
      : substep === 2
        ? handleContinueValeurs
        : handleFinishInterets;

  const helperBelowCta =
    submitError && substep !== 3
      ? "Pas de réseau ? Pas grave, on enregistre quand tu reviens."
      : substep === 3 && [interetsDraft["1"], interetsDraft["2"], interetsDraft["3"]].every((v) => !v)
        ? "Tu pourras compléter plus tard depuis ton profil."
        : substep === 1 && passionsDraft.length < MIN_PASSIONS
          ? "Sélectionne au moins 3 propositions."
          : substep === 2 && valeursDraft.length < MIN_VALEURS
            ? "Choisis-en au moins 3."
            : substep === 3
              ? "Tu peux finir quand tu veux."
              : "Tu peux continuer quand tu veux";

  const title =
    substep === 1
      ? copy.passionsTitle
      : substep === 2
        ? copy.valeursTitle
        : copy.interetsTitle;
  const subtitle =
    substep === 1
      ? copy.passionsSubtitle
      : substep === 2
        ? copy.valeursSubtitle
        : copy.interetsSubtitle;

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      {/* AC1 — header sticky */}
      <header className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-border bg-bg/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-bg/80">
        <button
          type="button"
          disabled
          aria-label="Retour (désactivé)"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md text-text-subtle"
        >
          <ChevronLeft aria-hidden className="h-5 w-5" />
        </button>
        <ProgressDots
          current={substep}
          onJumpTo={(target) => {
            const label =
              target === 1 ? "passions" : target === 2 ? "valeurs" : "centres d'intérêt";
            setSubstepWithAnnounce(target, label);
          }}
        />
        <button
          type="button"
          onClick={() => setSkipOpen(true)}
          className="inline-flex min-h-11 items-center rounded-md px-3 py-2 text-body-sm font-medium text-brand underline underline-offset-4 hover:text-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          data-testid="onboarding-skip-trigger"
        >
          Plus tard
        </button>
      </header>

      {/* AC1 — main */}
      <main
        id="onboarding-step1-main"
        className="mx-auto flex w-full max-w-[600px] flex-1 flex-col gap-4 px-4 py-6 sm:px-6"
        data-testid="onboarding-main"
      >
        <a
          href="#onboarding-step1-main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:rounded focus:bg-brand focus:px-3 focus:py-1 focus:text-white"
        >
          Aller au contenu principal
        </a>

        <h2 className="text-h2 font-semibold text-text">{title}</h2>
        <p className="text-body text-text-muted">{subtitle}</p>

        {substep === 1 ? (
          <PassionsPicker selected={passionsDraft} onChange={setPassionsDraft} />
        ) : substep === 2 ? (
          <ValeursPicker selected={valeursDraft} onChange={setValeursDraft} />
        ) : (
          <InteretsFreeForm
            value={interetsDraft}
            onChange={setInteretsDraft}
            placeholdersOverride={copy.interetsPlaceholders}
          />
        )}
      </main>

      {/* AC1 — footer sticky */}
      <footer className="sticky bottom-0 z-10 mt-auto border-t border-border bg-bg/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-bg/80 sm:px-6">
        <div className="mx-auto flex w-full max-w-[600px] flex-col gap-1">
          <Button
            type="button"
            size="lg"
            onClick={continueHandler}
            disabled={!canContinue || isSubmitting}
            data-testid="onboarding-continue"
            className="w-full sm:ml-auto sm:w-auto"
          >
            {isSubmitting ? "Enregistrement…" : continueLabel}
          </Button>
          <p
            className={cn(
              "text-center text-caption sm:text-right",
              submitError ? "text-warning" : "text-text-subtle",
            )}
            data-testid="onboarding-helper"
          >
            {helperBelowCta}
          </p>
        </div>
      </footer>

      <SkipDialog
        open={skipOpen}
        onOpenChange={setSkipOpen}
        onConfirm={handleSkipConfirm}
        isSubmitting={isSubmitting}
      />

      {/* AC6 — SR announcer for substep transitions. Kept outside the
          sticky header so its content update isn't conflated with the
          progress-dots role="step" update. */}
      <span aria-live="polite" className="sr-only" data-testid="onboarding-sr-announcer">
        {srMessage}
      </span>
    </div>
  );
}
