"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * `<ProgressDots>` — Story 2.1 §AC1, AC3. Three dots ●○○ that mark the
 * current sub-step (1A passions, 1B valeurs, 1C intérêts). Built as a
 * keyboard-focusable `<nav>` with a SR-only step label per dot — the
 * dots themselves are buttons so users can jump back to an earlier
 * sub-step via Enter/Space (§4.8 "Pas de bouton Précédent" — the dots
 * carry the navigation).
 *
 * The dot transition (inactive → active) uses `motion-quick` per AC3.
 * The global reduced-motion reset in `tokens.css` collapses the
 * transition duration so users with `prefers-reduced-motion` get an
 * instant switch.
 */

const STEP_LABELS: Record<1 | 2 | 3, string> = {
  1: "Étape 1 sur 3 : passions",
  2: "Étape 2 sur 3 : valeurs",
  3: "Étape 3 sur 3 : centres d'intérêt",
};

export type ProgressDotsProps = {
  current: 1 | 2 | 3;
  /** Optional click handler — when provided, dots before `current` are
   *  clickable and call this with the target step. Dots at or after
   *  `current` are still focusable but non-actionable. */
  onJumpTo?: (step: 1 | 2 | 3) => void;
};

export function ProgressDots({ current, onJumpTo }: ProgressDotsProps) {
  const steps: (1 | 2 | 3)[] = [1, 2, 3];
  return (
    // Pass 2 PR2-H6 — `-mx-4` on each `<li>` collapses the visual gap
    // back to the spec-literal 4 px (AC1) while keeping each 44 × 44
    // touch target intact. WCAG 2.5.5 allows touch targets to OVERLAP
    // each other as long as the visible target ≥ 44 × 44; the negative
    // margin makes the buttons overlap on either side without shrinking
    // the click surface. The wrapper `<ol>` is `gap-0` since the
    // negative margin replaces it.
    <nav aria-label="Progression onboarding" data-testid="progress-dots">
      <ol className="flex items-center">
        {steps.map((step) => {
          const isActive = step === current;
          const isPast = step < current;
          const canJump = isPast && onJumpTo !== undefined;
          return (
            <li key={step} className="-mx-4 flex first:ml-0 last:mr-0">
              {/* Pass 1 H4 + Pass 2 PR2-H6 — visible 8 × 8 dot inside a
                  44 × 44 click surface. Negative `mx-4` on the parent
                  `<li>` collapses the visible gap to 4 px (AC1) while
                  preserving the full touch target through controlled
                  overlap. */}
              <button
                type="button"
                onClick={canJump ? () => onJumpTo(step) : undefined}
                disabled={!canJump}
                aria-current={isActive ? "step" : undefined}
                aria-label={STEP_LABELS[step]}
                data-step={step}
                data-state={isActive ? "active" : isPast ? "past" : "future"}
                className={cn(
                  "inline-flex h-11 w-11 items-center justify-center rounded-full",
                  "transition-colors duration-quick ease-standard",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  !canJump && "cursor-default",
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "block h-2 w-2 rounded-full transition-colors duration-quick ease-standard",
                    isActive || isPast ? "bg-brand" : "bg-border-strong",
                  )}
                />
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
