"use client";

import * as React from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { LEVELS, type NiveauId } from "@/lib/onboarding/levels";

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
            announcerRef.current.textContent = item
              ? `${item.label} sélectionné. Les options correspondantes s'affichent maintenant.`
              : "";
          }
        }}
        className="flex flex-col gap-3"
      >
        {LEVELS.map((item) => {
          const isSelected = value === item.id;
          return (
            <div
              key={item.id}
              className={[
                "flex cursor-pointer items-center justify-between rounded-md border px-4 py-3",
                "min-h-[56px] bg-bg-2 transition-colors",
                isSelected
                  ? "border-brand bg-brand/5"
                  : "border-border hover:border-border-strong",
              ].join(" ")}
              onClick={() => onChange(item.id)}
            >
              <div className="flex flex-col gap-0.5">
                <Label
                  htmlFor={`niveau-${item.id}`}
                  className="cursor-pointer text-body font-medium"
                >
                  {item.label}
                </Label>
                <p className="text-body-sm text-text-muted">{item.description}</p>
              </div>
              <RadioGroupItem
                id={`niveau-${item.id}`}
                value={item.id}
                className="shrink-0"
              />
            </div>
          );
        })}
      </RadioGroup>
    </fieldset>
  );
}
