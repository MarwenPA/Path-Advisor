"use client";

import * as React from "react";
import { Check, Copy } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { cn } from "@/lib/utils";
import type { ScoreVocationnelProps, Signal } from "./types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Clamp to [0,100] and round to an integer (guards NaN / out-of-range / floats). */
function normaliseScore(score: number): number {
  if (!Number.isFinite(score)) return 0;
  return Math.min(100, Math.max(0, Math.round(score)));
}

type BadgeVariant = "success" | "warning" | "muted";

function scoreBadgeVariant(score: number): BadgeVariant {
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "muted";
}

// ---------------------------------------------------------------------------
// ScoreChip — score badge with semantic colour (AC1, AC6)
// ---------------------------------------------------------------------------

interface ScoreChipProps {
  score: number;
  large?: boolean;
  reducedMotion: boolean;
}

function ScoreChip({ score, large, reducedMotion }: ScoreChipProps) {
  const value = normaliseScore(score);
  return (
    <Badge
      variant={scoreBadgeVariant(value)}
      className={cn(
        "font-mono tabular-nums",
        // `large` (comparison variant) must win over the base text size, so the
        // base does not set a size here — the ternary is the single source.
        large ? "text-body" : "text-body-sm",
        !reducedMotion && "transition-colors duration-quick",
      )}
      aria-label={`Compatible à ${value} % avec ce métier`}
      style={{ fontFeatureSettings: '"tnum"' }}
    >
      {value}&thinsp;/&thinsp;100
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// CopyButton — clipboard action with live feedback (AC5, AC6)
// ---------------------------------------------------------------------------

interface CopyButtonProps {
  text: string;
  metiersName: string;
  disabled?: boolean;
}

function CopyButton({ text, metiersName, disabled }: CopyButtonProps) {
  const { copy, status, errorMessage } = useCopyToClipboard();
  const copied = status === "copied";
  const toastMessage =
    status === "copied"
      ? "Phrase copiée — colle-la où tu veux"
      : status === "error" && errorMessage
        ? errorMessage
        : null;

  return (
    <span className="relative inline-flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={() => copy(text)}
        disabled={disabled}
        aria-label={`Copier la phrase défendable pour ${metiersName}`}
        className={cn(
          "inline-flex items-center gap-1 rounded px-1.5 py-1 text-body-sm text-text-subtle",
          "hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:pointer-events-none disabled:opacity-50",
          "transition-colors duration-instant",
        )}
      >
        {copied ? <Check size={14} aria-hidden /> : <Copy size={14} aria-hidden />}
        <span className="sr-only">{copied ? "Copié" : "Copier"}</span>
      </button>

      {/*
        Single live region: announces the copy result to screen readers AND is
        the visible toast. One region avoids the double announcement that two
        separate role="status" + role="alert" nodes caused. It auto-dismisses
        when the hook resets `status` to "idle" after 2 s (RESET_DELAY_MS).
      */}
      {toastMessage && (
        <span
          role="status"
          aria-live="polite"
          className="absolute right-0 top-full z-10 mt-1 w-max max-w-xs rounded-md border border-border bg-card px-3 py-1.5 text-caption text-text shadow-sm"
        >
          {toastMessage}
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// SignalChips — signal buttons (AC1, AC3, AC6)
// ---------------------------------------------------------------------------

interface SignalChipsProps {
  signals: Signal[];
  maxVisible: number;
  onSignalClick?: (signalId: string) => void;
}

function SignalChips({ signals, maxVisible, onSignalClick }: SignalChipsProps) {
  const visible = signals.slice(0, maxVisible);
  const extra = signals.length - maxVisible;

  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label="Signaux contributifs">
      {visible.map((s) => (
        <Badge
          key={s.id}
          asChild
          variant="outline"
          className="cursor-pointer transition-colors duration-instant"
        >
          <button
            type="button"
            aria-label={`Signal contributif : ${s.label}`}
            onClick={() => onSignalClick?.(s.id)}
          >
            {s.label}
          </button>
        </Badge>
      ))}
      {extra > 0 && (
        <Badge variant="outline" className="text-text-subtle">
          +{extra} autres
        </Badge>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ScoreVocationnel — main component (AC1–AC7)
// ---------------------------------------------------------------------------

export function ScoreVocationnel({
  metierId,
  metiersName,
  score,
  phraseRecopiable,
  signals,
  variant,
  confidenceLevel,
  onSignalClick,
  onExplainClick,
}: ScoreVocationnelProps) {
  const reducedMotion = usePrefersReducedMotion();
  const isCompact = variant === "compact";
  const isExpanded = variant === "expanded";
  const isComparison = variant === "comparison";
  const isIndicative = confidenceLevel === "indicative";

  const maxSignals = isCompact ? 2 : 8;
  const trimmedPhrase = phraseRecopiable.trim();
  const hasPhrase = trimmedPhrase.length > 0;

  const phrase = (
    <p
      className={cn(
        "flex-1 text-body italic text-text",
        isCompact && "line-clamp-1",
      )}
      aria-label={
        hasPhrase
          ? `Phrase défendable pour ${metiersName} : ${trimmedPhrase}`
          : `Aucune phrase défendable disponible pour ${metiersName}`
      }
    >
      {hasPhrase ? <>&ldquo;{trimmedPhrase}&rdquo;</> : <span className="text-text-muted not-italic">Phrase à venir</span>}
    </p>
  );

  return (
    <article
      data-metier-id={metierId}
      className={cn(
        "flex flex-col gap-3 rounded-lg border border-border bg-card p-4 shadow-sm",
        isCompact && "max-h-40 max-w-[360px] overflow-hidden",
        isComparison && "h-full flex-1",
      )}
      aria-label={`Score vocationnel : ${metiersName}`}
    >
      {/* Header — nom métier + chip score */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5">
          <h3 className="text-h3 font-semibold leading-tight text-text">{metiersName}</h3>
          {isIndicative && (
            <span className="text-caption text-text-muted" aria-label="Score indicatif">
              indicatif
            </span>
          )}
        </div>
        <ScoreChip score={score} large={isComparison} reducedMotion={reducedMotion} />
      </div>

      {/* Body — phrase recopiable + bouton Copier */}
      <div className="flex items-start gap-2">
        {isCompact && hasPhrase ? (
          <Tooltip className="flex-1">
            <TooltipTrigger asChild>{phrase}</TooltipTrigger>
            <TooltipContent>{trimmedPhrase}</TooltipContent>
          </Tooltip>
        ) : (
          phrase
        )}
        <CopyButton text={trimmedPhrase} metiersName={metiersName} disabled={!hasPhrase} />
      </div>

      {/* Footer — chips signaux */}
      <SignalChips signals={signals} maxVisible={maxSignals} onSignalClick={onSignalClick} />

      {/* "Pourquoi ce score ?" — expanded only, always present (AC3) */}
      {isExpanded && (
        <button
          type="button"
          onClick={() => onExplainClick?.()}
          className={cn(
            "self-start text-body-sm text-brand underline-offset-2",
            "hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          )}
        >
          → Pourquoi ce score ?
        </button>
      )}
    </article>
  );
}

// ---------------------------------------------------------------------------
// ScoreVocationnelComparison — AC4 layout wrapper (2 cards côte à côte)
// ---------------------------------------------------------------------------

interface ScoreVocationnelComparisonProps {
  /** Exactly two cards to compare. Each is rendered with variant="comparison". */
  items: [
    Omit<ScoreVocationnelProps, "variant">,
    Omit<ScoreVocationnelProps, "variant">,
  ];
  onSignalClick?: (signalId: string) => void;
  onExplainClick?: () => void;
}

/**
 * AC4 — renders two `ScoreVocationnel` cards side by side.
 *
 * - Mobile: horizontal snap-scroll (swipe between the 2 cards).
 * - Desktop (≥1024 px / `lg`): 2-column grid with equal height
 *   (`items-stretch` + `h-full` on each card).
 */
export function ScoreVocationnelComparison({
  items,
  onSignalClick,
  onExplainClick,
}: ScoreVocationnelComparisonProps) {
  return (
    <div
      role="group"
      aria-label="Comparaison de deux métiers"
      className={cn(
        // Mobile: snap scroll carousel.
        "flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2",
        // Desktop: equal-height 2-column grid.
        "lg:grid lg:grid-cols-2 lg:items-stretch lg:overflow-visible",
      )}
    >
      {items.map((item) => (
        <div
          key={item.metierId}
          className="min-w-[85%] shrink-0 snap-center lg:min-w-0 lg:shrink"
        >
          <ScoreVocationnel
            {...item}
            variant="comparison"
            onSignalClick={item.onSignalClick ?? onSignalClick}
            onExplainClick={item.onExplainClick ?? onExplainClick}
          />
        </div>
      ))}
    </div>
  );
}
