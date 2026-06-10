"use client";

import * as React from "react";
import { Check } from "lucide-react";

import { MAX_VALEURS, MIN_VALEURS, VALEURS } from "@/lib/onboarding/referentials";
import { cn } from "@/lib/utils";

/**
 * `<ValeursPicker>` — Story 2.1 §AC3. Sub-step 1B.
 *
 * Vertical list of 12 large cards (touch target ≥ 56 px). Multi-select
 * with bounds 3 ≤ selection ≤ 5; over the cap, non-selected cards
 * atténuent (aria-disabled + visual 60% opacity) per AC3 last clause.
 *
 * Implemented as `role="group"` of `role="checkbox"` buttons (same
 * pattern as `PassionsPicker`) so screen readers expose the "3 sur 5
 * maximum" cardinality via the orchestrator's live region without
 * having to re-announce on every selection.
 */

export type ValeursPickerProps = {
  selected: readonly string[];
  onChange: (next: readonly string[]) => void;
};

export function ValeursPicker({ selected, onChange }: ValeursPickerProps) {
  const selectedSet = React.useMemo(() => new Set(selected), [selected]);
  const isAtMax = selected.length >= MAX_VALEURS;
  const atOrAboveMinimum = selected.length >= MIN_VALEURS;

  const handleToggle = (id: string) => {
    if (selectedSet.has(id)) {
      onChange(selected.filter((existing) => existing !== id));
      return;
    }
    if (isAtMax) return;
    onChange([...selected, id]);
  };

  return (
    <div className="flex flex-col gap-4">
      <ul
        role="group"
        aria-label="Valeurs personnelles"
        aria-describedby="valeurs-helper"
        className="flex flex-col gap-3"
        data-testid="valeurs-list"
      >
        {VALEURS.map((valeur) => {
          const isSelected = selectedSet.has(valeur.id);
          const isDisabled = !isSelected && isAtMax;
          return (
            <li key={valeur.id}>
              <button
                type="button"
                role="checkbox"
                aria-checked={isSelected}
                aria-disabled={isDisabled || undefined}
                onClick={() => handleToggle(valeur.id)}
                disabled={isDisabled}
                data-valeur-id={valeur.id}
                className={cn(
                  "flex w-full items-start gap-3 rounded-md border bg-bg-2 px-4 py-4 text-left",
                  "min-h-14 transition-colors duration-instant ease-standard",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  isSelected
                    ? "border-brand bg-brand/5"
                    : "border-border hover:bg-bg-3",
                  isDisabled && "cursor-not-allowed opacity-60",
                )}
              >
                <div className="flex-1">
                  <p className="text-body font-medium text-text">{valeur.label}</p>
                  <p className="text-body-sm text-text-muted">{valeur.description}</p>
                </div>
                <Check
                  aria-hidden
                  className={cn(
                    "mt-0.5 h-5 w-5 shrink-0",
                    isSelected ? "text-brand opacity-100" : "opacity-0",
                  )}
                />
              </button>
            </li>
          );
        })}
      </ul>

      {/* Pass 1 M4 — dedicated warning helper next to the list when the
          5-max is reached. */}
      {isAtMax ? (
        <p
          role="note"
          className="text-caption text-warning"
          data-testid="valeurs-max-helper"
        >
          Maximum {MAX_VALEURS} — désélectionne pour en changer.
        </p>
      ) : null}

      {/* Counter. Pass 1 M3 — `aria-live` removed; the orchestrator owns
          the AC9 threshold announcement. */}
      <p
        id="valeurs-helper"
        className={cn(
          "self-end text-caption",
          atOrAboveMinimum ? "text-success" : "text-text-subtle",
        )}
        data-testid="valeurs-counter"
      >
        {atOrAboveMinimum
          ? `${selected.length} / ${MIN_VALEURS} minimum atteint`
          : `${selected.length} / ${MIN_VALEURS} minimum`}
      </p>
    </div>
  );
}
