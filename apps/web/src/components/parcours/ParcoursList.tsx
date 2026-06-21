"use client";

import { useState } from "react";
import type { Parcours } from "@/lib/api/parcours";

// ─── Niveau badge mapping ──────────────────────────────────────────────────────

export const NIVEAU_BADGE: Record<string, string> = {
  troisieme_bac_pro: "Bac Pro",
  terminale_generale: "Terminale",
  terminale_technologique: "Terminale Techno",
  terminale_pro: "Terminale Pro",
  bts: "BTS",
  but: "BUT",
  licence: "Licence",
  autre: "Autre",
};

// ─── Admission dates display ───────────────────────────────────────────────────

function AdmissionDates({
  affelnetDates,
  parcoursupDates,
  niveauScolaire,
}: {
  affelnetDates: Record<string, string> | null;
  parcoursupDates: Record<string, string> | null;
  niveauScolaire: string;
}) {
  // For lycée pro (bac pro) tracks, show affelnet dates; otherwise show parcoursup dates
  const isAffelnet = niveauScolaire === "troisieme_bac_pro" || niveauScolaire === "terminale_pro";
  const dates = isAffelnet ? affelnetDates : parcoursupDates;
  const platform = isAffelnet ? "Affelnet" : "Parcoursup";

  if (!dates || Object.keys(dates).length === 0) {
    return null;
  }

  return (
    <div className="mt-1 text-xs text-muted-foreground" data-testid="admission-dates">
      <span className="font-medium">{platform} : </span>
      {dates.open && <span>ouverture {dates.open}</span>}
      {dates.close && <span> — clôture {dates.close}</span>}
      {dates.results && <span> — résultats {dates.results}</span>}
    </div>
  );
}

// ─── Single parcours card ──────────────────────────────────────────────────────

function ParcoursCard({ parcours }: { parcours: Parcours }) {
  const badgeLabel = NIVEAU_BADGE[parcours.niveau_scolaire] ?? parcours.niveau_scolaire;

  return (
    <div className="rounded-lg border bg-card p-4" data-testid={`parcours-card-${parcours.id}`}>
      {/* Header row: label + badge */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium leading-tight">
          {parcours.label || parcours.target_school_name || "Parcours"}
        </span>
        {parcours.niveau_scolaire && (
          <span
            className="shrink-0 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700"
            data-testid={`niveau-badge-${parcours.id}`}
          >
            {badgeLabel}
          </span>
        )}
      </div>

      {/* Target school */}
      {parcours.target_school_name && (
        <p className="mt-1 text-xs text-muted-foreground">
          Objectif : {parcours.target_school_name}
        </p>
      )}

      {/* Admission dates */}
      <AdmissionDates
        affelnetDates={parcours.target_school_affelnet_dates}
        parcoursupDates={parcours.target_school_parcoursup_dates}
        niveauScolaire={parcours.niveau_scolaire}
      />

      {/* Pathway steps summary */}
      {parcours.nodes.length > 0 && (
        <ol
          className="mt-3 space-y-1"
          aria-label={`Étapes du parcours ${parcours.label || "principal"}`}
        >
          {parcours.nodes.map((node, index) => (
            <li
              key={node.id}
              className="flex items-center gap-2 text-xs text-muted-foreground"
              data-testid={`parcours-node-${node.id}`}
            >
              <span
                className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-semibold"
                aria-hidden
              >
                {index + 1}
              </span>
              <span>{node.label}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

// ─── ParcoursList ──────────────────────────────────────────────────────────────

export interface ParcoursListProps {
  parcours: Parcours[];
  /** Optional: profession name for the heading */
  professionName?: string;
}

export function ParcoursList({ parcours, professionName }: ParcoursListProps) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  if (parcours.length === 0) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="parcours-empty">
        Aucun parcours disponible pour ce métier.
      </p>
    );
  }

  const [defaultParcours, ...alternatives] = parcours;

  return (
    <div className="space-y-4" data-testid="parcours-list">
      {professionName && (
        <h2 className="text-base font-semibold">Parcours pour {professionName}</h2>
      )}

      {/* Default / recommended parcours */}
      <ParcoursCard parcours={defaultParcours} />

      {/* Alternatives — collapsed by default */}
      {alternatives.length > 0 && (
        <div>
          <button
            type="button"
            className="flex items-center gap-1 text-sm text-primary underline underline-offset-2"
            onClick={() => setShowAlternatives((v) => !v)}
            aria-expanded={showAlternatives}
            data-testid="toggle-alternatives-btn"
          >
            {showAlternatives
              ? "Masquer les autres chemins"
              : `Voir d'autres chemins (${alternatives.length})`}
          </button>

          {showAlternatives && (
            <div className="mt-3 space-y-3" data-testid="alternatives-list">
              {alternatives.map((p) => (
                <div key={p.id} className="flex flex-col gap-1">
                  {/* Badge visible even in alternatives list header */}
                  <div className="flex items-center gap-2">
                    {p.niveau_scolaire && (
                      <span
                        className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700"
                        data-testid={`alt-badge-${p.id}`}
                      >
                        {NIVEAU_BADGE[p.niveau_scolaire] ?? p.niveau_scolaire}
                      </span>
                    )}
                    {p.is_default && (
                      <span className="text-xs text-muted-foreground">
                        (recommandé pour ce niveau)
                      </span>
                    )}
                  </div>
                  <ParcoursCard parcours={p} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
