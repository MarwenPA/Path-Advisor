// TODO(story-4-9): replace with GraphParcours once the real graph component lands.

"use client";

import type { ParcoursNode } from "./types";

const NODE_TYPE_LABELS: Record<string, string> = {
  start: "Départ",
  intermediate: "Étape",
  target: "Objectif",
  diplome: "Diplôme",
  ecole: "École",
  stage: "Stage",
  concours: "Concours",
};

const NODE_TYPE_COLORS: Record<string, string> = {
  start: "bg-blue-100 text-blue-800 border-blue-300",
  target: "bg-green-100 text-green-800 border-green-300",
  intermediate: "bg-gray-100 text-gray-700 border-gray-300",
  diplome: "bg-purple-100 text-purple-800 border-purple-300",
  ecole: "bg-amber-100 text-amber-800 border-amber-300",
  stage: "bg-orange-100 text-orange-800 border-orange-300",
  concours: "bg-red-100 text-red-800 border-red-300",
};

interface GraphParcoursPlaceholderProps {
  nodes: ParcoursNode[];
}

export function GraphParcoursPlaceholder({ nodes }: GraphParcoursPlaceholderProps) {
  return (
    <div aria-label="Étapes du parcours" className="relative pl-4">
      <ol className="space-y-0">
        {nodes.map((node, index) => {
          const isLast = index === nodes.length - 1;
          const colorClass = NODE_TYPE_COLORS[node.type] ?? NODE_TYPE_COLORS["intermediate"];
          const typeLabel = NODE_TYPE_LABELS[node.type] ?? node.type;

          return (
            <li key={node.id} className="flex items-start gap-3">
              {/* Vertical connector line */}
              <div className="flex flex-col items-center">
                <div
                  className={`mt-1 h-3 w-3 flex-shrink-0 rounded-full border-2 ${
                    node.type === "start"
                      ? "border-blue-600 bg-blue-500"
                      : node.type === "target"
                        ? "border-green-600 bg-green-500"
                        : "border-gray-500 bg-gray-400"
                  }`}
                  aria-hidden="true"
                />
                {!isLast && (
                  <div
                    className="my-1 w-px flex-1 bg-gray-300"
                    style={{ minHeight: "2rem" }}
                    aria-hidden="true"
                  />
                )}
              </div>
              {/* Node content */}
              <div className="min-w-0 flex-1 pb-6">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${colorClass}`}
                    aria-label={`Type: ${typeLabel}`}
                  >
                    {typeLabel}
                  </span>
                  <span className="text-sm font-medium text-gray-900">{node.label}</span>
                </div>
                {node.duration_label && (
                  <p className="mt-0.5 text-xs text-muted-foreground">{node.duration_label}</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
