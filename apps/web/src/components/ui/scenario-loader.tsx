"use client";

import * as React from "react";
import {
  AlertTriangle,
  BookOpen,
  FileImage,
  Loader2,
  Lock,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import {
  track,
  type ScenarioLoaderContext as AnalyticsScenarioLoaderContext,
} from "@/lib/analytics/events";
import { cn } from "@/lib/utils";

/*
 * ScenarioLoader — Couche 3 Path-Advisor primitive (Story 2.8).
 *
 * Transforms any > 1 s wait into a sequenced narration (illustration + rotating
 * phrase + linear progress bar + opt-in fallback). Anti-spinner-nu primitive:
 * no opaque > 1 s wait in the product should ship a bare Material/iOS spinner.
 *
 * Consumers (Q2): Story 2.3 OCR ~30 s, Story 3.1 reco compute ~3-5 s,
 * Story 5.x payment confirm ~2-3 s, Epic 6 export PNG/PDF.
 *
 * Design decisions verrouillées (Story 2.8 §4.4):
 *   - No `onProgress` — bar is purely linear over `estimatedSeconds`.
 *     Real progress (file upload) belongs to shadcn `<Progress value>`.
 *   - No "Annuler" CTA — `onFallback` is the only exit; it does NOT cancel
 *     the server-side job, only signals the consumer to swap views.
 *   - Last phrase persists. No loop, no return to phrase 1 (anti-cirque).
 *   - `role="status"` (not `alert`) — wait is expected, not critical.
 */

export type ScenarioLoaderContext = AnalyticsScenarioLoaderContext;

export type ScenarioLoaderProps = {
  /** Sequential phrases, min 1 max 6. Each phrase visible
   *  `clamp(estimatedSeconds / phrases.length, 4, 12)` seconds.
   *  Memoise on the caller side — re-passing a new array reference
   *  resets the loader to phrase 0. */
  phrases: readonly string[];
  /** Total estimated wait in seconds — drives phrase timing and bar fill. */
  estimatedSeconds: number;
  /** Semantic context — drives icon, SR label and analytics. */
  context?: ScenarioLoaderContext;
  /** If provided, surfaces a tertiary "Faire autrement" button under the
   *  overrun warning. The button does NOT unmount the loader — that is the
   *  caller's responsibility. */
  onFallback?: () => void;
  fallbackLabel?: string;
  /** Caller-controlled completion — snaps the bar to 100 % and freezes the
   *  final phrase. Emits `scenario_loader_completed` once. */
  isComplete?: boolean;
  /** Caller-controlled error — fades the loader out so the caller can
   *  unmount it cleanly (typically replacing with a `<GracefulFallback>`).
   *  Emits `scenario_loader_errored` once. */
  isError?: boolean;
};

const CONTEXT_MAP: Record<ScenarioLoaderContext, { icon: LucideIcon; srLabel: string }> = {
  ocr: { icon: BookOpen, srLabel: "Analyse des bulletins en cours" },
  reco: { icon: Sparkles, srLabel: "Calcul des recommandations en cours" },
  export: { icon: FileImage, srLabel: "Génération du fichier en cours" },
  payment: { icon: Lock, srLabel: "Confirmation du paiement en cours" },
  generic: { icon: Loader2, srLabel: "Chargement en cours" },
};

const PHRASE_MIN_MS = 4_000;
const PHRASE_MAX_MS = 12_000;

function clampMs(value: number): number {
  return Math.min(PHRASE_MAX_MS, Math.max(PHRASE_MIN_MS, value));
}

function normalizePhrases(phrases: readonly string[]): readonly string[] {
  if (process.env.NODE_ENV !== "production") {
    if (phrases.length === 0) {
      throw new Error("[ScenarioLoader] `phrases` must contain at least one entry");
    }
    if (phrases.length > 6) {
      throw new Error("[ScenarioLoader] `phrases` accepts at most 6 entries");
    }
    return phrases;
  }
  // Production: silent fallbacks per Story 2.8 §4.5.
  if (phrases.length === 0) return [""];
  if (phrases.length > 6) return phrases.slice(0, 6);
  return phrases;
}

function normalizeSeconds(seconds: number): number {
  if (process.env.NODE_ENV !== "production") {
    if (seconds <= 0) {
      throw new Error("[ScenarioLoader] `estimatedSeconds` must be > 0");
    }
    if (seconds > 300) {
      console.warn(
        "[ScenarioLoader] estimatedSeconds > 300 — usually an estimation bug, accepted as-is",
      );
    }
    return seconds;
  }
  return seconds <= 0 ? 5 : seconds;
}

export function ScenarioLoader({
  phrases,
  estimatedSeconds,
  context = "generic",
  onFallback,
  fallbackLabel = "Faire autrement",
  isComplete = false,
  isError = false,
}: ScenarioLoaderProps) {
  const safePhrases = React.useMemo(() => normalizePhrases(phrases), [phrases]);
  const safeSeconds = React.useMemo(() => normalizeSeconds(estimatedSeconds), [estimatedSeconds]);
  const phrasesKey = safePhrases.join("");

  const phraseDurationMs = React.useMemo(
    () => clampMs((safeSeconds * 1000) / safePhrases.length),
    [safeSeconds, safePhrases.length],
  );

  const [phraseIndex, setPhraseIndex] = React.useState(0);
  const [showWarning, setShowWarning] = React.useState(false);
  const [isFadingOut, setIsFadingOut] = React.useState(false);

  const startedAtRef = React.useRef<number | null>(null);
  const completedEmittedRef = React.useRef(false);
  const erroredEmittedRef = React.useRef(false);
  const warningEmittedRef = React.useRef(false);

  const prefersReducedMotion = usePrefersReducedMotion();

  // Caller swapped the phrases array (rare; see §4.5) — reset state during
  // render so the new phrase shows on the same frame. React batches these
  // setStates into the in-flight render, no cascade.
  const [prevPhrasesKey, setPrevPhrasesKey] = React.useState(phrasesKey);
  if (prevPhrasesKey !== phrasesKey) {
    setPrevPhrasesKey(phrasesKey);
    setPhraseIndex(0);
    setShowWarning(false);
    setIsFadingOut(false);
  }

  // Stamp / reset the per-session bookkeeping in an effect (ref mutations in
  // render are forbidden by the React 19 lint rule). Declared BEFORE the
  // analytics effects so it commits first — by the time completion/error
  // /warning effects re-run for the new phrases-key, the emission flags are
  // already false.
  React.useEffect(() => {
    startedAtRef.current = Date.now();
    completedEmittedRef.current = false;
    erroredEmittedRef.current = false;
    warningEmittedRef.current = false;
  }, [phrasesKey]);

  // Chained setTimeout for phrase advancement — prefer over setInterval to
  // avoid drift on throttled tabs and mobile (Story 2.8 §4.2).
  React.useEffect(() => {
    if (safePhrases.length <= 1) return;
    if (isComplete || isError) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let index = 0;
    const tick = () => {
      if (cancelled) return;
      if (index >= safePhrases.length - 1) return;
      index += 1;
      setPhraseIndex(index);
      timer = setTimeout(tick, phraseDurationMs);
    };
    timer = setTimeout(tick, phraseDurationMs);
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [phrasesKey, phraseDurationMs, safePhrases.length, isComplete, isError]);

  // Overrun warning + analytics — fires at most once per session
  // (phrasesKey scoped). Including phrasesKey in the deps lets a rare
  // mid-mount phrases swap start a fresh warning timer.
  React.useEffect(() => {
    if (isComplete || isError) return;
    const timer = setTimeout(() => {
      setShowWarning(true);
      if (!warningEmittedRef.current) {
        warningEmittedRef.current = true;
        track({
          name: "scenario_loader_estimation_exceeded",
          context,
          estimated_seconds: safeSeconds,
          actual_seconds_at_warning: safeSeconds,
        });
      }
    }, safeSeconds * 1000);
    return () => clearTimeout(timer);
  }, [context, safeSeconds, isComplete, isError, phrasesKey]);

  // Completion side-effects (idempotent per session).
  React.useEffect(() => {
    if (!isComplete || isError) return;
    if (completedEmittedRef.current) return;
    completedEmittedRef.current = true;
    setPhraseIndex(safePhrases.length - 1);
    const startedAt = startedAtRef.current ?? Date.now();
    track({
      name: "scenario_loader_completed",
      context,
      actual_seconds: (Date.now() - startedAt) / 1000,
      estimated_seconds: safeSeconds,
    });
  }, [isComplete, isError, context, safeSeconds, safePhrases.length, phrasesKey]);

  // Error side-effects (idempotent per session). `isError` wins over `isComplete`.
  React.useEffect(() => {
    if (!isError) return;
    if (erroredEmittedRef.current) return;
    erroredEmittedRef.current = true;
    setIsFadingOut(true);
    const startedAt = startedAtRef.current ?? Date.now();
    track({
      name: "scenario_loader_errored",
      context,
      actual_seconds: (Date.now() - startedAt) / 1000,
    });
  }, [isError, context, phrasesKey]);

  const { icon: Icon, srLabel } = CONTEXT_MAP[context];
  const currentPhrase = safePhrases[phraseIndex] ?? "";
  const barWidth = isComplete ? 100 : 0;
  const showParticle = !prefersReducedMotion && !isComplete && !isError;
  const dataState = isError
    ? "error"
    : isComplete
      ? "complete"
      : showWarning
        ? "warning"
        : "running";

  return (
    <section
      role="status"
      aria-live="polite"
      aria-busy={!isComplete && !isError}
      aria-label={srLabel}
      data-context={context}
      data-state={dataState}
      className={cn(
        "flex w-full flex-col items-center justify-center gap-8 px-4 py-12",
        "transition-opacity duration-quick ease-standard",
        isFadingOut ? "scale-[0.98] opacity-0" : "opacity-100",
      )}
    >
      <div className="relative">
        <div
          aria-hidden
          className="flex h-24 w-24 items-center justify-center rounded-full border border-border bg-bg-2"
        >
          <Icon className="h-10 w-10 text-text-muted" aria-hidden />
        </div>
        {showParticle ? (
          <span
            aria-hidden
            data-testid="scenario-loader-particle"
            className="absolute right-0 top-0 h-[10px] w-[10px] animate-scenario-loader-particle rounded-full bg-brand"
          />
        ) : null}
      </div>

      <p
        data-testid="scenario-loader-phrase"
        className="min-h-7 text-center text-h2 font-semibold text-text transition-opacity duration-quick ease-standard"
      >
        {currentPhrase}
      </p>

      <div className="flex w-full max-w-[280px] flex-col gap-3">
        <div
          aria-hidden
          className="h-1 w-full overflow-hidden rounded-full bg-bg-3"
          data-testid="scenario-loader-bar"
        >
          <div
            className="h-full rounded-full bg-brand"
            style={{
              width: `${barWidth}%`,
              transitionProperty: "width",
              transitionTimingFunction: "linear",
              transitionDuration: isComplete ? "var(--motion-quick)" : `${safeSeconds}s`,
            }}
          />
        </div>
        <p className="text-center text-caption text-text-subtle">
          Estimation : ~{safeSeconds} secondes
        </p>
      </div>

      {showWarning && !isComplete && !isError ? (
        <EstimationWarning onFallback={onFallback} fallbackLabel={fallbackLabel} />
      ) : null}

      {/* Final-state announcer — separate from the running region so SRs
          announce "Terminé" / error message exactly once. */}
      <span role="status" aria-live="polite" className="sr-only">
        {isComplete && !isError ? "Terminé." : ""}
        {isError ? "Un problème est survenu, options disponibles ci-dessous." : ""}
      </span>
    </section>
  );
}

function EstimationWarning({
  onFallback,
  fallbackLabel,
}: {
  onFallback?: () => void;
  fallbackLabel: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2" data-testid="scenario-loader-warning">
      <div
        role="status"
        className="flex max-w-[320px] items-center gap-2 rounded-lg border border-warning bg-warning-bg px-4 py-3 text-body-sm text-text"
      >
        <AlertTriangle className="h-[18px] w-[18px] shrink-0 text-warning" aria-hidden />
        <span>Ça prend un peu plus de temps que prévu, on continue.</span>
      </div>
      {onFallback ? (
        <button
          type="button"
          onClick={onFallback}
          className="min-h-11 px-3 py-2 text-body-sm font-medium text-brand underline underline-offset-4 hover:text-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {fallbackLabel}
        </button>
      ) : null}
    </div>
  );
}

export default ScenarioLoader;
