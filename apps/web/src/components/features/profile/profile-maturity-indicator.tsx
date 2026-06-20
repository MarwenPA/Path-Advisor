"use client";

import * as React from "react";
import { BookOpen, ChevronDown, ChevronUp, FileText, Heart, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { MaturityLevel } from "@/lib/profile/maturity";

// ---------------------------------------------------------------------------
// Public types — AC1
// ---------------------------------------------------------------------------

export type { MaturityLevel };

export type MaturityNextAction = {
  label: string;
  benefit: string;
  onClick: () => void;
  icon: "bulletins" | "level" | "passions" | "specialites";
};

export type ProfileMaturityIndicatorProps = {
  level: MaturityLevel;
  nextActions: readonly MaturityNextAction[];
  variant?: "profile-header" | "dashboard-card" | "inline-compact";
  showCallToAction?: boolean;
};

// ---------------------------------------------------------------------------
// Copy — locked per AC3 / 4.2
// ---------------------------------------------------------------------------

const LEVEL_LABELS: Record<MaturityLevel, string> = {
  base: "Profil de base",
  enriched: "Profil enrichi",
  complete: "Profil complet",
};

const LEVEL_DESCRIPTIONS: Record<MaturityLevel, string> = {
  base: "Tu as l'essentiel pour des recos indicatives — toutes les explorations sont ouvertes.",
  enriched: "Tu débloques les stats personnalisées sur tes parcours.",
  complete: "Tu profites de toutes les features — recos affinées, stats précises, parcours ciblés.",
};

// ---------------------------------------------------------------------------
// Runtime dev validation — forbidden words (AC3 / 4.3)
// ---------------------------------------------------------------------------

const FORBIDDEN_WORDS = [
  "incomplet",
  "incomplète",
  "manque",
  "manquant",
  "manquante",
  "%",
  "pourcentage",
  "raté",
  "ratée",
  "tu rates",
  "il te reste",
  "tu n'as pas encore",
  "termine ton profil",
  "complète ton profil",
  "finalise",
];

function devCheckCopy(text: string): void {
  if (process.env.NODE_ENV !== "production") {
    const lower = text.toLowerCase();
    for (const word of FORBIDDEN_WORDS) {
      if (lower.includes(word)) {
        console.warn(
          `[ProfileMaturityIndicator] Forbidden word found in copy: "${word}" in "${text}". ` +
            "See Story 2.7 § 4.3 — Mots interdits dans le copy."
        );
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Icon map
// ---------------------------------------------------------------------------

const ACTION_ICONS: Record<MaturityNextAction["icon"], React.ReactNode> = {
  bulletins: <FileText className="size-5 shrink-0" aria-hidden />,
  level: <BookOpen className="size-5 shrink-0" aria-hidden />,
  passions: <Heart className="size-5 shrink-0" aria-hidden />,
  specialites: <Sparkles className="size-5 shrink-0" aria-hidden />,
};

// ---------------------------------------------------------------------------
// NextActionsList — shared sub-component (AC4)
// ---------------------------------------------------------------------------

type NextActionsListProps = {
  actions: readonly MaturityNextAction[];
  listId: string;
};

function NextActionsList({ actions, listId }: NextActionsListProps) {
  return (
    <ul id={listId} className="mt-4 flex flex-col gap-3">
      {actions.map((action) => {
        devCheckCopy(action.label);
        devCheckCopy(action.benefit);
        return (
          <li key={action.label}>
            <button
              type="button"
              onClick={action.onClick}
              className={cn(
                "w-full flex items-center gap-3 rounded-md border border-border bg-card",
                "px-4 py-4 text-left min-h-[64px]",
                "hover:bg-muted hover:border-foreground/30",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                "transition-colors"
              )}
            >
              {ACTION_ICONS[action.icon]}
              <span className="flex-1 min-w-0">
                <span className="block font-medium text-sm text-foreground">{action.label}</span>
                <span className="block text-xs text-muted-foreground">{action.benefit}</span>
              </span>
              <ChevronDown className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            </button>
          </li>
        );
      })}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// MaturityProfileHeader — variant profile-header (AC3)
// ---------------------------------------------------------------------------

type HeaderVariantProps = {
  level: MaturityLevel;
  nextActions: readonly MaturityNextAction[];
  showCallToAction: boolean;
  uid: string;
};

function MaturityProfileHeader({ level, nextActions, showCallToAction, uid }: HeaderVariantProps) {
  const [expanded, setExpanded] = React.useState(false);
  const titleId = `maturity-title-${uid}`;
  const listId = `next-actions-${uid}`;

  return (
    <section
      role="region"
      aria-labelledby={titleId}
      className={cn(
        "w-full max-w-[1080px] rounded-lg border border-border bg-card",
        "p-6"
      )}
    >
      <span className="sr-only" aria-live="polite">
        {`Niveau de profil : ${LEVEL_LABELS[level]}.`}
      </span>

      <h3 id={titleId} className="text-xl font-semibold text-foreground">
        {LEVEL_LABELS[level]}
      </h3>
      <p className="mt-2 text-sm text-muted-foreground">{LEVEL_DESCRIPTIONS[level]}</p>

      {showCallToAction && nextActions.length > 0 && (
        <>
          <Button
            type="button"
            variant="secondary"
            className="mt-4"
            aria-expanded={expanded}
            aria-controls={listId}
            onClick={() => setExpanded((prev) => !prev)}
          >
            {expanded ? (
              <>
                <ChevronUp className="size-4" aria-hidden />
                Plier
              </>
            ) : (
              <>
                Voir comment compléter
                <ChevronDown className="size-4" aria-hidden />
              </>
            )}
          </Button>

          {expanded && (
            <NextActionsList actions={nextActions} listId={listId} />
          )}
        </>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// MaturityDashboardCard — variant dashboard-card (AC5)
// ---------------------------------------------------------------------------

function MaturityDashboardCard({ level, uid }: { level: MaturityLevel; uid: string }) {
  if (level === "complete") return null;

  return (
    <div
      className={cn(
        "flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between",
        "rounded-lg border border-border bg-card px-4 py-3"
      )}
      aria-label={`Niveau de profil : ${LEVEL_LABELS[level]}`}
    >
      <span className="text-sm text-foreground">
        <span className="font-medium">{LEVEL_LABELS[level]}</span>
        {" · "}
        <span className="text-muted-foreground">{LEVEL_DESCRIPTIONS[level]}</span>
      </span>
      <a
        href="/profile"
        className="text-sm text-primary hover:underline whitespace-nowrap"
      >
        Mon profil →
      </a>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MaturityInlineCompact — variant inline-compact (AC6)
// ---------------------------------------------------------------------------

function MaturityInlineCompact({ level }: { level: MaturityLevel }) {
  return (
    <a
      href="/profile"
      title={LEVEL_DESCRIPTIONS[level]}
      className={cn(
        "inline-flex items-center rounded-full border border-border bg-card",
        "px-3 py-1 text-sm text-foreground hover:bg-muted transition-colors"
      )}
    >
      {LEVEL_LABELS[level]}
    </a>
  );
}

// ---------------------------------------------------------------------------
// Public default export — ProfileMaturityIndicator (AC1)
// ---------------------------------------------------------------------------

const _uidCounter = 0;

export function ProfileMaturityIndicator({
  level,
  nextActions,
  variant = "profile-header",
  showCallToAction = level !== "complete",
}: ProfileMaturityIndicatorProps) {
  const uid = React.useId().replace(/:/g, "");

  // Runtime dev validation — runs eagerly on every render (AC3 / 4.3)
  if (process.env.NODE_ENV !== "production") {
    for (const action of nextActions) {
      devCheckCopy(action.label);
      devCheckCopy(action.benefit);
    }
  }

  if (variant === "dashboard-card") {
    return <MaturityDashboardCard level={level} uid={uid} />;
  }

  if (variant === "inline-compact") {
    return <MaturityInlineCompact level={level} />;
  }

  return (
    <MaturityProfileHeader
      level={level}
      nextActions={nextActions}
      showCallToAction={showCallToAction}
      uid={uid}
    />
  );
}

export default ProfileMaturityIndicator;
