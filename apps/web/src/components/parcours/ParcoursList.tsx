"use client";

import { useState } from "react";

import { GraphParcoursPlaceholder } from "./GraphParcoursPlaceholder";
import type { Parcours } from "./types";

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

  // Collect school nodes for the school grid (nodes with a schoolSlug).
  const schoolNodes = defaultParcours.nodes.filter((n) => n.schoolSlug);

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
        <GraphParcoursPlaceholder nodes={defaultParcours.nodes} />

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
          {alternatives.map((p) => (
            <li key={p.id} className="rounded-lg border p-4">
              <p className="font-medium">{p.target_school_name ?? p.target_school}</p>
              {p.target_school_city && (
                <p className="text-xs text-muted-foreground">{p.target_school_city}</p>
              )}
              <p className="mt-1 text-sm text-muted-foreground">{p.nodes.length} étapes</p>
              <div className="mt-3">
                <GraphParcoursPlaceholder nodes={p.nodes} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
