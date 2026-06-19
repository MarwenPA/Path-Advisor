"use client";

import * as React from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { LEVELS, TRACKS_3EME, FILIERES_LYCEE, POSTBAC_YEARS, type NiveauId } from "@/lib/onboarding/levels";

const BRANCH_OPTION_COUNT: Partial<Record<NiveauId, number>> = {
  college_3eme: TRACKS_3EME.length,
  lycee_2nde: FILIERES_LYCEE.length,
  lycee_1ere: FILIERES_LYCEE.length,
  lycee_terminale: FILIERES_LYCEE.length,
  postbac: POSTBAC_YEARS.length,
};

type NiveauPickerProps = {
  value: NiveauId | null;
  onChange: (id: NiveauId) => void;
  announcerRef?: React.RefObject<HTMLDivElement>;
};

export function NiveauPicker({ value, onChange, announcerRef }: NiveauPickerProps) {
  return (
    <fieldset className="flex flex-col gap-4">
      <legend className="sr-only">Niveau scolaire</legend>
      <RadioGroup
        value={value ?? ""}
        onValueChange={(v) => {
          onChange(v as NiveauId);
          // AC10 — aria-live announce branch change
          if (announcerRef?.current) {
            const item = LEVELS.find((l) => l.id === v);
            if (item) {
              const count = BRANCH_OPTION_COUNT[item.id as NiveauId];
              const countHint = count !== undefined ? ` ${count} option${count > 1 ? "s" : ""} disponible${count > 1 ? "s" : ""}.` : "";
              announcerRef.current.textContent = `${item.label} sélectionné.${countHint} Les options correspondantes s'affichent maintenant.`;
            } else {
              announcerRef.current.textContent = "";
            }
          }
        }}
        className="flex flex-col gap-3"
      >
        {LEVELS.map((item) => {
          const isSelected = value === item.id;
          return (
            <Label
              key={item.id}
              htmlFor={`niveau-${item.id}`}
              className={[
                "flex cursor-pointer items-center justify-between rounded-md border px-4 py-3",
                "min-h-[56px] bg-bg-2 transition-colors",
                isSelected
                  ? "border-brand bg-brand/5"
                  : "border-border hover:border-border-strong",
              ].join(" ")}
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-body font-medium">{item.label}</span>
                <p className="text-body-sm text-text-muted">{item.description}</p>
              </div>
              <RadioGroupItem
                id={`niveau-${item.id}`}
                value={item.id}
                className="shrink-0"
              />
            </Label>
          );
        })}
      </RadioGroup>
    </fieldset>
  );
}
