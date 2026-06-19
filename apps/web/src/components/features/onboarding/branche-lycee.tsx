"use client";

import * as React from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import {
  FILIERES_LYCEE,
  SOUS_FILIERES_TECHNO,
  type NiveauId,
  type FiliereId,
  type SousFiliereId,
  expectedSpecCount,
  requiresSousFiliere,
} from "@/lib/onboarding/levels";
import { SpecialitesPicker } from "./specialites-picker";

type BrancheLyceeProps = {
  level: NiveauId;
  filiere: FiliereId | null;
  sousFiliere: SousFiliereId | null;
  specialites: string[];
  onFiliereChange: (f: FiliereId) => void;
  onSousFiliereChange: (sf: SousFiliereId | null) => void;
  onToggleSpecialite: (id: string) => void;
  announcerRef?: React.RefObject<HTMLDivElement>;
};

export function BrancheLycee({
  level,
  filiere,
  sousFiliere,
  specialites,
  onFiliereChange,
  onSousFiliereChange,
  onToggleSpecialite,
  announcerRef,
}: BrancheLyceeProps) {
  const expectedCount = filiere ? expectedSpecCount(level, filiere) : null;
  const needsSousFiliere = filiere ? requiresSousFiliere(level, filiere) : false;

  const isNo2ndeSpec = level === "lycee_2nde" && (filiere === "general" || filiere === "techno");

  return (
    <section
      aria-labelledby="branche-lycee-heading"
      className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-200"
    >
      <div>
        <h3 id="branche-lycee-heading" className="text-h3 font-semibold text-text">
          Ta filière au lycée
        </h3>
      </div>

      <fieldset>
        <legend className="sr-only">Filière</legend>
        <RadioGroup
          value={filiere ?? ""}
          onValueChange={(v) => {
            onFiliereChange(v as FiliereId);
            if (announcerRef?.current) {
              const item = FILIERES_LYCEE.find((f) => f.id === v);
              announcerRef.current.textContent = item
                ? `${item.label} sélectionné.${v === "techno" && needsSousFiliere ? " Choisis ta sous-filière." : ""}`
                : "";
            }
          }}
          className="flex flex-col gap-3"
        >
          {FILIERES_LYCEE.map((item) => {
            const isSelected = filiere === item.id;
            return (
              <Label
                key={item.id}
                htmlFor={`filiere-${item.id}`}
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
                <RadioGroupItem id={`filiere-${item.id}`} value={item.id} className="shrink-0" />
              </Label>
            );
          })}
        </RadioGroup>
      </fieldset>

      {/* 2nde général/techno — no spécialités yet */}
      {isNo2ndeSpec && (
        <p className="text-body-sm text-text-muted">
          En 2nde, tu n&apos;as pas encore choisi tes spés. On te demandera plus tard.
        </p>
      )}

      {/* Techno → sous-filière required for 1ère/Terminale */}
      {needsSousFiliere && (
        <fieldset className="flex flex-col gap-3">
          <legend className="text-body font-medium text-text">Ta sous-filière techno</legend>
          {!sousFiliere && (
            <p className="text-body-sm text-text-muted">Précise ta sous-filière techno.</p>
          )}
          <RadioGroup
            value={sousFiliere ?? ""}
            onValueChange={(v) => onSousFiliereChange(v as SousFiliereId)}
            className="flex flex-col gap-2"
          >
            {SOUS_FILIERES_TECHNO.map((sf) => {
              const isSelected = sousFiliere === sf.id;
              return (
                <Label
                  key={sf.id}
                  htmlFor={`sf-${sf.id}`}
                  className={[
                    "flex cursor-pointer items-center justify-between rounded-md border px-4 py-2.5",
                    "min-h-[44px] bg-bg-2 transition-colors",
                    isSelected ? "border-brand bg-brand/5" : "border-border hover:border-border-strong",
                  ].join(" ")}
                >
                  <div>
                    <span className="text-body font-medium">{sf.id}</span>
                    <p className="text-body-sm text-text-muted">{sf.description}</p>
                  </div>
                  <RadioGroupItem id={`sf-${sf.id}`} value={sf.id} className="shrink-0" />
                </Label>
              );
            })}
          </RadioGroup>
        </fieldset>
      )}

      {/* Spécialités */}
      {filiere && expectedCount !== null && !isNo2ndeSpec && (
        <SpecialitesPicker
          filiere={filiere}
          selected={specialites}
          expectedCount={expectedCount}
          onToggle={onToggleSpecialite}
          announcerRef={announcerRef}
        />
      )}
    </section>
  );
}
