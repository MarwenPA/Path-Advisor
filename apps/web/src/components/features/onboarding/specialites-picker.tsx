"use client";

import * as React from "react";
import { SPECIALITES_LYCEE, SPECIALITES_BAC_PRO, type FiliereId } from "@/lib/onboarding/levels";

type SpecialitesPickerProps = {
  filiere: FiliereId;
  selected: string[];
  expectedCount: number;
  onToggle: (id: string) => void;
  announcerRef?: React.RefObject<HTMLDivElement>;
};

export function SpecialitesPicker({
  filiere,
  selected,
  expectedCount,
  onToggle,
  announcerRef,
}: SpecialitesPickerProps) {
  const items = filiere === "pro" ? SPECIALITES_BAC_PRO : SPECIALITES_LYCEE;
  const count = selected.length;
  const isComplete = count === expectedCount;
  const isOver = count > expectedCount;

  const handleToggle = (id: string) => {
    onToggle(id);
    if (announcerRef?.current) {
      const item = items.find((s) => s.id === id);
      if (!item) return;
      const isNowSelected = !selected.includes(id);
      const newCount = isNowSelected ? count + 1 : count - 1;
      announcerRef.current.textContent = isNowSelected
        ? `${item.shortLabel ?? item.label} sélectionné, ${newCount} sur ${expectedCount} spécialité${expectedCount > 1 ? "s" : ""} à choisir.`
        : `${item.shortLabel ?? item.label} désélectionné, ${newCount} sur ${expectedCount}.`;
    }
  };

  return (
    <div
      role="group"
      aria-labelledby="spes-heading"
      className="flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <p id="spes-heading" className="text-body-sm text-text-muted">
          {filiere === "pro"
            ? "Sélectionne ta spécialité bac pro."
            : `Sélectionne tes ${expectedCount} spécialité${expectedCount > 1 ? "s" : ""}.`}
        </p>
        <span
          className={[
            "text-body-sm font-medium tabular-nums",
            isComplete ? "text-success" : isOver ? "text-warning" : "text-text-muted",
          ].join(" ")}
          aria-live="polite"
        >
          {count}/{expectedCount}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isSelected = selected.includes(item.id);
          const atCap = !isSelected && count >= expectedCount;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => !atCap && handleToggle(item.id)}
              aria-pressed={isSelected}
              disabled={atCap}
              className={[
                "rounded-full border px-3 py-1.5 text-body-sm font-medium transition-colors",
                "min-h-[44px] cursor-pointer",
                isSelected
                  ? "border-brand bg-brand text-white"
                  : atCap
                  ? "cursor-not-allowed border-border text-text-subtle opacity-40"
                  : "border-border bg-bg-2 text-text hover:border-brand",
              ].join(" ")}
            >
              {"shortLabel" in item ? (item as { shortLabel: string }).shortLabel : item.label}
            </button>
          );
        })}
      </div>

      {isOver && (
        <p className="text-body-sm text-warning" role="alert">
          Maximum {expectedCount} spécialité{expectedCount > 1 ? "s" : ""}.
        </p>
      )}
    </div>
  );
}
