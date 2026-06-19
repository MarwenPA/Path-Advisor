"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Step2Draft } from "@/hooks/use-onboarding-step-2";
import {
  LEVELS,
  FILIERES_LYCEE,
  TRACKS_3EME,
  POSTBAC_YEARS,
  POSTBAC_FORMATIONS,
  SOUS_FILIERES_TECHNO,
  SPECIALITES_LYCEE,
  SPECIALITES_BAC_PRO,
  calendarHint,
} from "@/lib/onboarding/levels";

type RecapCardProps = {
  draft: Step2Draft;
  onModify: () => void;
};

export function RecapCard({ draft, onModify }: RecapCardProps) {
  const levelItem = LEVELS.find((l) => l.id === draft.level);
  const filiereItem = FILIERES_LYCEE.find((f) => f.id === draft.filiere);
  const trackItem = TRACKS_3EME.find((t) => t.id === draft.intended_track);
  const yearItem = POSTBAC_YEARS.find((y) => y.id === draft.postbac_year);
  const formationItem = POSTBAC_FORMATIONS.find((f) => f.id === draft.postbac_formation_type);
  const sousFiliereItem = SOUS_FILIERES_TECHNO.find((sf) => sf.id === draft.sous_filiere_techno);

  const allSpecs = [...SPECIALITES_LYCEE, ...SPECIALITES_BAC_PRO];
  const specItems = draft.specialites
    .map((id) => ({ id, label: allSpecs.find((s) => s.id === id)?.shortLabel ?? id }));

  const hint = draft.level ? calendarHint(draft.level, draft.intended_track) : "";

  const headline = [
    levelItem?.label,
    draft.level === "college_3eme" && trackItem ? `Visée : ${trackItem.label}` : null,
    draft.level !== "college_3eme" && draft.level !== "postbac" && filiereItem
      ? filiereItem.label
      : null,
    draft.level === "postbac" && yearItem ? yearItem.label : null,
  ]
    .filter(Boolean)
    .join(" • ");

  return (
    <section aria-labelledby="recap-heading" className="flex flex-col gap-6">
      <div>
        <h2 id="recap-heading" className="text-h2 font-semibold text-text">
          Voilà ce que tu as déclaré
        </h2>
        <p className="mt-1 text-body text-text-muted">Tu peux modifier avant de continuer.</p>
      </div>

      <Card className="flex flex-col gap-4 bg-bg-2 p-6">
        <p className="text-body font-semibold text-text">{headline}</p>

        {sousFiliereItem && (
          <p className="text-body text-text">{sousFiliereItem.id} — {sousFiliereItem.description}</p>
        )}

        {specItems.length > 0 && (
          <div className="flex flex-col gap-1">
            <p className="text-body-sm text-text-muted">Tes spécialités :</p>
            <ul className="ml-4 list-disc">
              {specItems.map(({ id, label }) => (
                <li key={id} className="text-body">{label}</li>
              ))}
            </ul>
          </div>
        )}

        {draft.level === "postbac" && formationItem && (
          <p className="text-body text-text">{formationItem.label}</p>
        )}

        {hint && <p className="text-body-sm text-text-subtle">{hint}</p>}

        <div className="flex justify-end">
          <Button variant="ghost" size="sm" onClick={onModify} autoFocus>
            Modifier
          </Button>
        </div>
      </Card>
    </section>
  );
}
