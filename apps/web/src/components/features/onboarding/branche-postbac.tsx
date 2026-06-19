"use client";

import * as React from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { POSTBAC_YEARS, POSTBAC_FORMATIONS, type PostbacYearId, type PostbacFormationId } from "@/lib/onboarding/levels";

type BranchePostbacProps = {
  year: PostbacYearId | null;
  formationType: PostbacFormationId | null;
  onYearChange: (year: PostbacYearId) => void;
  onFormationChange: (type: PostbacFormationId) => void;
};

export function BranchePostbac({ year, formationType, onYearChange, onFormationChange }: BranchePostbacProps) {
  return (
    <section
      aria-labelledby="branche-postbac-heading"
      className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-200"
    >
      <div>
        <h3 id="branche-postbac-heading" className="text-h3 font-semibold text-text">
          Où tu en es dans tes études ?
        </h3>
        <p className="mt-1 text-body-sm text-text-muted">On adaptera nos suggestions à ton parcours.</p>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
        {/* Année */}
        <fieldset className="flex flex-1 flex-col gap-3">
          <legend className="text-body font-medium text-text">Ton niveau actuel</legend>
          <RadioGroup
            value={year ?? ""}
            onValueChange={(v) => onYearChange(v as PostbacYearId)}
            className="flex flex-col gap-2"
          >
            {POSTBAC_YEARS.map((item) => {
              const isSelected = year === item.id;
              return (
                <div
                  key={item.id}
                  className={[
                    "flex cursor-pointer items-center justify-between rounded-md border px-4 py-3",
                    "min-h-[44px] bg-bg-2 transition-colors",
                    isSelected ? "border-brand bg-brand/5" : "border-border hover:border-border-strong",
                  ].join(" ")}
                  onClick={() => onYearChange(item.id)}
                >
                  <Label htmlFor={`year-${item.id}`} className="cursor-pointer text-body">
                    {item.label}
                  </Label>
                  <RadioGroupItem id={`year-${item.id}`} value={item.id} className="shrink-0" />
                </div>
              );
            })}
          </RadioGroup>
        </fieldset>

        {/* Type de formation */}
        <div className="flex flex-1 flex-col gap-3">
          <label className="text-body font-medium text-text" htmlFor="postbac-formation">
            Ta situation actuelle
          </label>
          <Select value={formationType ?? ""} onValueChange={(v) => onFormationChange(v as PostbacFormationId)}>
            <SelectTrigger id="postbac-formation" className="w-full">
              <SelectValue placeholder="Sélectionne une option" />
            </SelectTrigger>
            <SelectContent>
              {POSTBAC_FORMATIONS.map((f) => (
                <SelectItem key={f.id} value={f.id}>
                  {f.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </section>
  );
}
