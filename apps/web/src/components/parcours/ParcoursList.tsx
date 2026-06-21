"use client";

import { useState } from "react";

import { GraphParcoursPlaceholder } from "./GraphParcoursPlaceholder";
import type { AdmissionStatInline, Parcours, ParcoursNode } from "./types";

// ---------------------------------------------------------------------------
// Inline admission stat helpers (Story 4.5 AC2)
// ---------------------------------------------------------------------------

const LABEL_BADGE_CLASS: Record<AdmissionStatInline["label"], string> = {
  audacieux: "text-red-700 bg-red-50",
  realiste: "text-blue-700 bg-blue-50",
  sur: "text-green-700 bg-green-50",
  estimation_indicative: "text-slate-700 bg-slate-50",
};

const LABEL_TEXT: Record<AdmissionStatInline["label"], string> = {
  audacieux: "pari audacieux",
  realiste: "pari réaliste",
  sur: "pari sûr",
  estimation_indicative: "estimation indicative",
};

/**
 * Renders an inline admission stat badge when node.admission_stat is present.
 * Hidden (renders nothing) when absent — UX-DR25.
 */
function NodeAdmissionStatBadge({ stat }: { stat: AdmissionStatInline }) {
  const badgeClass = LABEL_BADGE_CLASS[stat.label] ?? "text-slate-700 bg-slate-50";
  const labelText = LABEL_TEXT[stat.label] ?? stat.label;
  return (
    <span
      className={`mt-0.5 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badgeClass}`}
      data-testid="node-admission-stat-badge"
    >
      {stat.expected_proba}% &middot; {labelText}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Helpers to resolve nodes_with_stats or fall back to nodes
// ---------------------------------------------------------------------------

function getEnrichedNodes(parcours: Parcours): ParcoursNode[] {
  // Prefer nodes_with_stats (Story 4.5) if present; fall back to plain nodes.
  return parcours.nodes_with_stats ?? parcours.nodes;
}

// ---------------------------------------------------------------------------
// ParcoursList — Story 4.3 component + Story 4.5 inline stat
// ---------------------------------------------------------------------------

// ─── Niveau badge mapping (Story 4.7) ─────────────────────────────────────────

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

// ─── Admission dates display (Story 4.7) ──────────────────────────────────────

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

// ─── ParcoursList ──────────────────────────────────────────────────────────────

export interface ParcoursListProps {
  parcours: Parcours[];
  metiersSlug: string;
  /** Optional: profession name for the heading */
  professionName?: string;
}

export function ParcoursList({
  parcours,
  metiersSlug: _metiersSlug,
  professionName,
}: ParcoursListProps) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  if (parcours.length === 0) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="parcours-empty">
        Aucun parcours disponible pour ce métier pour l&apos;instant.
      </p>
    );
  }

  // Find default parcours (is_default=true) or fall back to first item.
  const defaultIndex = parcours.findIndex((p) => p.is_default);
  const effectiveDefaultIndex = defaultIndex >= 0 ? defaultIndex : 0;
  const defaultParcours = parcours[effectiveDefaultIndex];
  const alternatives = parcours.filter((_, i) => i !== effectiveDefaultIndex);
  const altCount = alternatives.length;

  // Use enriched nodes (with admission_stat if available — Story 4.5).
  const enrichedNodes = getEnrichedNodes(defaultParcours);

  // Collect school nodes for the school grid (nodes with a schoolSlug).
  const schoolNodes = enrichedNodes.filter((n) => n.schoolSlug);

  const defaultBadgeLabel =
    NIVEAU_BADGE[defaultParcours.niveau_scolaire] ?? defaultParcours.niveau_scolaire;

  return (
    <section aria-label="Parcours disponibles" data-testid="parcours-list">
      {professionName && (
        <h2 className="mb-3 text-base font-semibold">Parcours pour {professionName}</h2>
      )}
      {!professionName && <h2 className="mb-3 text-lg font-semibold">Parcours vers ce métier</h2>}

      {/* Default parcours */}
      <div
        className="mb-4 rounded-lg border p-4"
        data-testid={`parcours-card-${defaultParcours.id}`}
      >
        {/* Header: label/school + niveau badge */}
        <div className="mb-1 flex items-start justify-between gap-2">
          <p className="font-medium">
            {defaultParcours.label ||
              defaultParcours.target_school_name ||
              defaultParcours.target_school}
          </p>
          {defaultParcours.niveau_scolaire && (
            <span
              className="shrink-0 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700"
              data-testid={`niveau-badge-${defaultParcours.id}`}
            >
              {defaultBadgeLabel}
            </span>
          )}
        </div>

        {defaultParcours.target_school_city && (
          <p className="text-xs text-muted-foreground">{defaultParcours.target_school_city}</p>
        )}

        {/* Admission dates */}
        <AdmissionDates
          affelnetDates={defaultParcours.target_school_affelnet_dates}
          parcoursupDates={defaultParcours.target_school_parcoursup_dates}
          niveauScolaire={defaultParcours.niveau_scolaire}
        />

        {/* Graph placeholder — TODO(story-4-9): replace with GraphParcours */}
        <div className="mt-3">
          <GraphParcoursPlaceholder nodes={enrichedNodes} />
        </div>

        {/* School grid: cards for each node with a schoolSlug */}
        {schoolNodes.length > 0 && (
          <div className="mt-4">
            <h3 className="mb-2 text-sm font-semibold">Établissements sur ce parcours</h3>
            <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {schoolNodes.map((node) => (
                <li key={node.id}>
                  <a
                    href={`/schools/${node.schoolSlug}`}
                    className="block rounded border p-3 text-sm transition-colors hover:bg-accent"
                    aria-label={`Voir la fiche de ${node.label}`}
                  >
                    <span className="font-medium">{node.label}</span>
                    {/* Story 4.5 AC2 — inline admission stat badge */}
                    {node.admission_stat && <NodeAdmissionStatBadge stat={node.admission_stat} />}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Alternatives toggle button */}
      {altCount > 0 && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setShowAlternatives((v) => !v)}
            className="flex items-center gap-1 text-sm font-medium text-primary underline-offset-2 hover:underline"
            aria-expanded={showAlternatives}
            data-testid="toggle-alternatives-btn"
          >
            {showAlternatives
              ? "Masquer les autres chemins"
              : `Voir d'autres chemins (${altCount})`}
          </button>
        </div>
      )}

      {/* Alternative parcours list */}
      {showAlternatives && altCount > 0 && (
        <ul className="mt-3 space-y-3" data-testid="alternatives-list">
          {alternatives.map((p) => {
            const altEnrichedNodes = getEnrichedNodes(p);
            return (
              <li
                key={p.id}
                className="rounded-lg border p-4"
                data-testid={`parcours-card-${p.id}`}
              >
                {/* Badge + label */}
                <div className="mb-1 flex items-center gap-2">
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
                <p className="font-medium">{p.label || p.target_school_name || p.target_school}</p>
                {p.target_school_city && (
                  <p className="text-xs text-muted-foreground">{p.target_school_city}</p>
                )}
                <p className="mt-1 text-sm text-muted-foreground">{p.nodes.length} étapes</p>
                <div className="mt-3">
                  <GraphParcoursPlaceholder nodes={altEnrichedNodes} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
