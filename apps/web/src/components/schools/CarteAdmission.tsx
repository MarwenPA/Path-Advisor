"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import type { AdmissionStat } from "@/lib/api/schools";
import { apiFetch } from "@/lib/api/client";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/**
 * Human-readable display label for each qualitative admission category.
 * Lowercase per AC3 spec example ("pari audacieux", not "Pari Audacieux").
 */
const LABEL_DISPLAY: Record<AdmissionStat["label"], string> = {
  audacieux: "pari audacieux",
  realiste: "pari réaliste",
  sur: "pari sûr",
  estimation_indicative: "estimation indicative",
};

// ---------------------------------------------------------------------------
// Pure helper functions (exported for unit tests)
// ---------------------------------------------------------------------------

/**
 * Returns Tailwind color tokens for the given probability (AC2).
 *
 * Thresholds (spec §AC2):
 *   < 30  → red
 *   30–49 → orange
 *   50–70 → neutral/slate
 *   > 70  → green
 *
 * Every color token is doubled by a visible text label (UX-DR33 color-blind safety).
 * Input is clamped to [0, 100]; NaN/Infinity falls back to 0.
 */
export function getSemanticColor(proba: number): {
  text: string;
  badge: string;
  bgBadge: string;
} {
  // [High] Guard against NaN/Infinity/negative — clamp to valid [0,100] range
  const safe = Number.isFinite(proba) ? Math.max(0, Math.min(100, proba)) : 0;

  if (safe > 70) {
    return {
      text: "text-green-600",
      badge: "text-green-700",
      bgBadge: "bg-green-50",
    };
  }
  if (safe >= 50) {
    return {
      text: "text-slate-600",
      badge: "text-slate-700",
      bgBadge: "bg-slate-50",
    };
  }
  if (safe >= 30) {
    return {
      text: "text-orange-500",
      badge: "text-orange-700",
      bgBadge: "bg-orange-50",
    };
  }
  // safe < 30
  return {
    text: "text-red-600",
    badge: "text-red-700",
    bgBadge: "bg-red-50",
  };
}

/**
 * Returns the human-readable display text for a qualitative label.
 * Exported for unit tests.
 */
export function getLabelText(label: AdmissionStat["label"]): string {
  return LABEL_DISPLAY[label];
}

/**
 * Builds the aria-label for the component root (AC3).
 *
 * Format: "{proba} % d'admission à {schoolName} — {qualitativeLabel}. {action_lever if not null}"
 *
 * Example:
 *   buildAriaLabel(38, "INSA Lyon", "audacieux", "+ 2 points en maths feraient passer à 58 %")
 *   → "38 % d'admission à INSA Lyon — pari audacieux. + 2 points en maths feraient passer à 58 %."
 *
 * [Medium] Trailing punctuation on actionLever is stripped before appending to avoid double-periods.
 */
export function buildAriaLabel(
  proba: number,
  schoolName: string,
  label: AdmissionStat["label"],
  actionLever: string | null,
): string {
  const qualitative = LABEL_DISPLAY[label];
  const base = `${proba} % d'admission à ${schoolName} — ${qualitative}.`;
  if (!actionLever) return base;
  // [Medium] Strip trailing punctuation to avoid double-periods (e.g. "lever." → "lever")
  const lever = actionLever.replace(/[.!?]+$/, "");
  return `${base} ${lever}.`;
}

// ---------------------------------------------------------------------------
// UpdateBadge — internal sub-component (AC4)
// ---------------------------------------------------------------------------

interface UpdateBadgeProps {
  updatedAt?: string;
  previousProba?: number;
  expectedProba: number;
  schoolName?: string;
  schoolSlug?: string;
}

/**
 * Renders a "+N pts" badge when the admission stat was updated within the
 * last 24 hours AND a previous probability is available.
 *
 * Uses sessionStorage to suppress the badge after the first view per session
 * (so it reappears in a new browser session — intentionally sessionStorage,
 * not localStorage, per spec anti-patterns).
 */
function UpdateBadge({
  updatedAt,
  previousProba,
  expectedProba,
  schoolName,
  schoolSlug,
}: UpdateBadgeProps) {
  const [visible, setVisible] = React.useState(false);
  // [Medium] isMounted ref prevents setState after unmount (StrictMode double-invoke safe)
  const isMountedRef = React.useRef(true);

  React.useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  React.useEffect(() => {
    if (!updatedAt || previousProba == null) return;

    // [High] Guard against invalid date string
    const ts = new Date(updatedAt).getTime();
    if (isNaN(ts)) return;

    const isRecent = Date.now() - ts < 24 * 60 * 60 * 1000;
    if (!isRecent) return;

    // [Medium] delta === 0 means no change — skip badge
    const delta = Math.round(expectedProba - previousProba);
    if (delta === 0) return;

    // [High] Use schoolName as fallback instead of hardcoded 'unknown'
    const slugKey = schoolSlug ?? schoolName ?? "school";
    const storageKey = `carte_admission_badge_seen_${slugKey}`;
    try {
      if (sessionStorage.getItem(storageKey)) return;
      sessionStorage.setItem(storageKey, "1");
    } catch {
      // sessionStorage may be unavailable in some contexts (SSR, private mode)
    }

    if (isMountedRef.current) {
      setVisible(true);
    }
  }, [updatedAt, previousProba, expectedProba, schoolSlug, schoolName]);

  if (!visible || previousProba == null) return null;

  // [Low] Float delta rounded to integer
  const delta = Math.round(expectedProba - previousProba);
  if (delta === 0) return null;
  const sign = delta >= 0 ? "+" : "";

  return (
    <span
      aria-label={`Mise à jour : ${sign}${delta} points`}
      className="absolute right-0 top-0 animate-fade-in rounded-full bg-green-500 px-2 py-0.5 text-xs font-bold text-white"
    >
      {sign}
      {delta} pts
    </span>
  );
}

// ---------------------------------------------------------------------------
// CarteAdmission — main component
// ---------------------------------------------------------------------------

interface CarteAdmissionProps {
  admissionStat: AdmissionStat;
  variant: "large" | "medium" | "small" | "export";
  schoolName: string;
  schoolSlug?: string;
  className?: string;
}

/**
 * Revolut-style admission probability card.
 *
 * - 4 variants: large (graph node), medium (FicheEcole), small (comparison list), export (PNG capture)
 * - Semantic colors + text labels (UX-DR33 color-blind safety)
 * - RGAA AA compliant aria-label
 * - "+N pts" update badge when stat changed in last 24h (AC4)
 * - Indicative footnote for incomplete profiles (AC5)
 */
export function CarteAdmission({
  admissionStat,
  variant,
  schoolName,
  schoolSlug,
  className,
}: CarteAdmissionProps) {
  const { expected_proba, label, context_line, action_lever, updated_at, previous_proba } =
    admissionStat;

  const colors = getSemanticColor(expected_proba);
  const labelText = getLabelText(label);
  const ariaLabel = buildAriaLabel(expected_proba, schoolName, label, action_lever);

  const isExport = variant === "export";

  // Stat number sizing per variant
  const statSizeClass = cn(
    variant === "large" && "text-5xl font-bold",
    variant === "medium" && "text-3xl font-bold",
    variant === "small" && "text-2xl font-semibold",
    isExport && "text-3xl font-bold",
  );

  // Label badge text sizing per variant
  const labelSizeClass = cn(
    variant === "large" && "text-lg",
    variant === "medium" && "text-base",
    variant === "small" && "text-sm",
    isExport && "text-base",
  );

  return (
    <div
      role="region"
      aria-label={ariaLabel}
      data-export={isExport ? "" : undefined}
      className={cn("relative flex flex-col gap-1", isExport && "pointer-events-none", className)}
    >
      {/* Stat + badge row */}
      <div className="relative flex items-center gap-2">
        {/* Primary stat — aria-hidden because the root aria-label covers it */}
        <span aria-hidden="true" className={cn(statSizeClass, colors.text)}>
          {expected_proba} %
        </span>

        {/* Qualitative label badge — always visible (UX-DR33) */}
        <span
          aria-hidden="true"
          className={cn("rounded-full px-2 py-0.5", labelSizeClass, colors.badge, colors.bgBadge)}
        >
          {labelText}
        </span>

        {/* Update badge (+N pts) — AC4 */}
        <UpdateBadge
          updatedAt={updated_at}
          previousProba={previous_proba}
          expectedProba={expected_proba}
          schoolSlug={schoolSlug}
          schoolName={schoolName}
        />
      </div>

      {/* Context line — [Low] line-clamp-2 on small variant to prevent overflow */}
      <p className={cn("text-sm text-muted-foreground", variant === "small" && "line-clamp-2")}>
        {context_line}
      </p>

      {/* Action lever — hidden in export variant (AC1) */}
      {action_lever && !isExport && <p className="text-sm text-slate-700">{action_lever}</p>}

      {/* Indicative footnote — AC5 */}
      {label === "estimation_indicative" && (
        <p className="mt-1 text-xs italic text-slate-500">
          Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner.
        </p>
      )}
    </div>
  );
}
