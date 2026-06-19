"use client";

import * as React from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { TRACKS_3EME, type Track3emeId } from "@/lib/onboarding/levels";

type Branche3emeProps = {
  value: Track3emeId | null;
  onChange: (track: Track3emeId) => void;
};

export function Branche3eme({ value, onChange }: Branche3emeProps) {
  return (
    <section aria-labelledby="branche-3eme-heading" className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div>
        <h3 id="branche-3eme-heading" className="text-h3 font-semibold text-text">
          Et après la 3ème, tu vises plutôt quoi ?
        </h3>
        <p className="mt-1 text-body-sm text-text-muted">Tu peux changer plus tard, t&apos;inquiète.</p>
      </div>

      <fieldset>
        <legend className="sr-only">Orientation après la 3ème</legend>
        <RadioGroup
          value={value ?? ""}
          onValueChange={(v) => onChange(v as Track3emeId)}
          className="flex flex-col gap-3"
        >
          {TRACKS_3EME.map((track) => {
            const isSelected = value === track.id;
            return (
              <Label
                key={track.id}
                htmlFor={`track-${track.id}`}
                className={[
                  "flex cursor-pointer items-center justify-between rounded-md border px-4 py-3",
                  "min-h-[56px] bg-bg-2 transition-colors",
                  isSelected
                    ? "border-brand bg-brand/5"
                    : "border-border hover:border-border-strong",
                ].join(" ")}
              >
                <div className="flex flex-col gap-0.5">
                  <span className="text-body font-medium">{track.label}</span>
                  <p className="text-body-sm text-text-muted">{track.description}</p>
                </div>
                <RadioGroupItem id={`track-${track.id}`} value={track.id} className="shrink-0" />
              </Label>
            );
          })}
        </RadioGroup>
      </fieldset>
    </section>
  );
}
