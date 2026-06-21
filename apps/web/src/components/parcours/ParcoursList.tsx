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

interface ParcoursListProps {
  parcours: Parcours[];
  metiersSlug: string;
}

export function ParcoursList({ parcours, metiersSlug: _metiersSlug }: ParcoursListProps) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  if (parcours.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
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

  return (
    <section aria-label="Parcours disponibles">
      <h2 className="mb-3 text-lg font-semibold">Parcours vers ce métier</h2>

      {/* Default parcours */}
      <div className="mb-4 rounded-lg border p-4">
        <div className="mb-3">
          <p className="font-medium">
            {defaultParcours.target_school_name ?? defaultParcours.target_school}
          </p>
          {defaultParcours.target_school_city && (
            <p className="text-xs text-muted-foreground">{defaultParcours.target_school_city}</p>
          )}
          {defaultParcours.niveau_scolaire && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              Niveau: {defaultParcours.niveau_scolaire.replace(/_/g, " ")}
            </p>
          )}
        </div>

        {/* Graph placeholder — TODO(story-4-9): replace with GraphParcours */}
        <GraphParcoursPlaceholder nodes={enrichedNodes} />

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

      {/* Alternatives toggle button — hidden if no alternatives */}
      {altCount > 0 && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setShowAlternatives((v) => !v)}
            className="text-sm font-medium text-primary underline-offset-2 hover:underline"
            aria-expanded={showAlternatives}
          >
            {showAlternatives
              ? "Masquer les autres chemins"
              : `Voir d'autres chemins (${altCount})`}
          </button>
        </div>
      )}

      {/* Alternative parcours list */}
      {showAlternatives && altCount > 0 && (
        <ul className="mt-3 space-y-3">
          {alternatives.map((p) => {
            const altEnrichedNodes = getEnrichedNodes(p);
            return (
              <li key={p.id} className="rounded-lg border p-4">
                <p className="font-medium">{p.target_school_name ?? p.target_school}</p>
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
