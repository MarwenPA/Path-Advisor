"use client";

import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type StatPersonnelleState = "compatible" | "a_renforcer" | "au_dessus" | null;

interface StatPersonnelleProps {
  /** Compatibility state. null/undefined renders nothing (UX-DR25). */
  state: StatPersonnelleState;
  subject?: string;
  currentGrade?: number;
  targetGrade?: number;
  className?: string;
}

// ---------------------------------------------------------------------------
// Config map — avoids long conditionals, typed for exhaustive safety
// ---------------------------------------------------------------------------

const STATE_CONFIG = {
  compatible: {
    label: "Compatible",
    description: "Ton niveau correspond aux attentes de cette formation.",
    colorText: "text-green-700",
    colorBg: "bg-green-50",
    colorBorder: "border-green-200",
    icon: "✓",
  },
  a_renforcer: {
    label: "A renforcer",
    description: "Quelques points a travailler pour maximiser tes chances.",
    colorText: "text-yellow-700",
    colorBg: "bg-yellow-50",
    colorBorder: "border-yellow-200",
    icon: "~",
  },
  au_dessus: {
    label: "Au-dessus",
    description: "Ton niveau depasse les attentes de cette formation.",
    colorText: "text-blue-700",
    colorBg: "bg-blue-50",
    colorBorder: "border-blue-200",
    icon: "↑",
  },
} as const satisfies Record<
  NonNullable<StatPersonnelleState>,
  {
    label: string;
    description: string;
    colorText: string;
    colorBg: string;
    colorBorder: string;
    icon: string;
  }
>;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Additive compatibility indicator for students with complete profiles.
 *
 * UX-DR25: null/undefined state renders nothing — no placeholder, no gap,
 * no empty DOM node. The parent never needs a conditional wrapper.
 *
 * Color-blind safe: icon + text label + color (three redundant cues).
 * role="region" (not role="status") to avoid live-region noise on mount.
 */
export function StatPersonnelle({
  state,
  subject,
  currentGrade,
  targetGrade,
  className,
}: StatPersonnelleProps) {
  // UX-DR25: strict null guard — returns nothing, no DOM node
  if (state === null || state === undefined) return null;

  const config = STATE_CONFIG[state];
  const subjectSuffix = subject ? ` en ${subject}` : "";

  return (
    <div
      role="region"
      aria-label={config.label + subjectSuffix}
      className={cn("rounded-lg border p-3", config.colorBg, config.colorBorder, className)}
    >
      <div className="flex items-center gap-2">
        <span aria-hidden="true" className={cn("text-lg", config.colorText)}>
          {config.icon}
        </span>
        <div>
          <p className={cn("text-sm font-medium", config.colorText)}>
            {config.label}
            {subjectSuffix}
          </p>
          <p className="text-xs text-muted-foreground">{config.description}</p>
          {currentGrade !== undefined && targetGrade !== undefined && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              {currentGrade}/20 vs {targetGrade}/20 requis
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
