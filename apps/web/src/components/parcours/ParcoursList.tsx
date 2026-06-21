"use client";

import type { ParcoursNode, ParcoursEdge, AdmissionStatInline } from "./types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Label badge color helpers (consistent with CarteAdmission)
// ---------------------------------------------------------------------------

function getLabelBadgeClass(label: AdmissionStatInline["label"]): string {
  const map: Record<AdmissionStatInline["label"], string> = {
    audacieux: "text-red-700 bg-red-50",
    realiste: "text-blue-700 bg-blue-50",
    sur: "text-green-700 bg-green-50",
    estimation_indicative: "text-slate-700 bg-slate-50",
  };
  return map[label];
}

function getLabelText(label: AdmissionStatInline["label"]): string {
  const map: Record<AdmissionStatInline["label"], string> = {
    audacieux: "pari audacieux",
    realiste: "pari réaliste",
    sur: "pari sûr",
    estimation_indicative: "estimation indicative",
  };
  return map[label];
}

// ---------------------------------------------------------------------------
// NodeCard — renders a single step card
// ---------------------------------------------------------------------------

interface NodeCardProps {
  node: ParcoursNode;
  step: number;
  total: number;
}

function NodeCard({ node, step, total }: NodeCardProps) {
  const isTarget = node.type === "target";
  const isStart = node.type === "start";

  return (
    <li
      data-testid={`parcours-node-${node.id}`}
      className={cn(
        "flex flex-col gap-1 rounded-lg border px-4 py-3",
        isTarget && "border-blue-200 bg-blue-50",
        isStart && "border-slate-200 bg-slate-50",
        !isTarget && !isStart && "border-gray-200 bg-white",
      )}
    >
      {/* Step label */}
      <span className="text-xs font-medium text-muted-foreground">
        Étape {step} / {total}
      </span>

      {/* Node label */}
      <span className={cn("text-sm font-semibold", isTarget && "text-blue-900")}>{node.label}</span>

      {/* Inline admission stat — Story 4.5 AC2 */}
      {node.admission_stat && (
        <span
          className={cn(
            "mt-0.5 inline-flex items-center gap-1.5 text-xs font-medium",
            getLabelBadgeClass(node.admission_stat.label),
            "rounded-full px-2 py-0.5",
          )}
          data-testid={`node-admission-stat-${node.id}`}
        >
          {node.admission_stat.expected_proba}% &middot; {getLabelText(node.admission_stat.label)}
        </span>
      )}
    </li>
  );
}

// ---------------------------------------------------------------------------
// ParcoursList — accessible list representation of a parcours
// ---------------------------------------------------------------------------

export interface ParcoursListProps {
  nodes: ParcoursNode[];
  edges?: ParcoursEdge[];
  targetSchool: string;
  className?: string;
}

/**
 * Accessible list view of a parcours with inline admission stats.
 *
 * Story 4.5 — AC2: each target node displays `expected_proba% · label` when
 * `node.admission_stat` is present. If null, nothing extra is shown (UX-DR25).
 */
export function ParcoursList({ nodes, targetSchool, className }: ParcoursListProps) {
  if (nodes.length === 0) {
    return <p className="text-sm text-muted-foreground">Aucune étape de parcours disponible.</p>;
  }

  return (
    <section
      aria-label={`Parcours vers ${targetSchool}`}
      className={cn("space-y-2", className)}
      data-testid="parcours-list"
    >
      <ol aria-label="Étapes du parcours" className="space-y-2">
        {nodes.map((node, i) => (
          <NodeCard key={node.id} node={node} step={i + 1} total={nodes.length} />
        ))}
      </ol>
    </section>
  );
}
