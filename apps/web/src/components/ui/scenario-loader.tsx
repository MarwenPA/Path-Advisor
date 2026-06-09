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
  // Drives the linear progress fill. Seeded to 0 on mount / phrasesKey
  // change, then RAF'd to 100 so the CSS transition (duration = safeSeconds)
  // runs visually. Snaps to 100 in motion-quick on isComplete. Frozen on
  // isError so the loader fades out from wherever the wait got to.
  const [barWidth, setBarWidth] = React.useState(0);

  const startedAtRef = React.useRef<number | null>(null);
  const completedEmittedRef = React.useRef(false);
  const erroredEmittedRef = React.useRef(false);
  const warningEmittedRef = React.useRef(false);
  // Mirror of `phraseIndex` so the chained-setTimeout effect can resume from
  // the current phrase when its deps change mid-flight (e.g. caller revises
  // estimatedSeconds). Without this, the effect's closure restarts at 0
  // and jumps the user BACKWARDS — violating the anti-cirque invariant.
  //
  // Pass 2 PR3 — the sync runs as an unkeyed `useEffect` (post-commit, every
  // render) rather than a render-time `phraseIndexRef.current = phraseIndex`
  // mutation. React 19's `react-hooks/refs` lint forbids ref writes during
  // render; the unkeyed effect is the supported pattern and is declared
  // FIRST so it commits before any other effect that reads the ref.
  const phraseIndexRef = React.useRef(0);
  React.useEffect(() => {
    phraseIndexRef.current = phraseIndex;
  });

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

  // Stamp / reset the per-session bookkeeping. Declared BEFORE the analytics
  // effects so it commits first — by the time completion/warning effects
  // re-run for the new phrases-key, their emission flags are already false.
  //
  // H4 + M8 — `!isError` gate: an in-flight error must not have its emission
  // latch cleared by an upstream phrases-swap (otherwise the error effect
  // re-emits `scenario_loader_errored` a second time). The error recovery
  // effect below handles the legitimate `isError: true → false` transition.
  React.useEffect(() => {
    if (isError) return;
    startedAtRef.current = Date.now();
    completedEmittedRef.current = false;
    // erroredEmittedRef is intentionally NOT cleared here — it is owned by
    // the recovery effect below, which needs to detect the prior-error →
    // recovered transition (`erroredEmittedRef.current === true && !isError`)
    // and only then re-arm the latch. Clearing it here would race with that
    // detection and leave `isFadingOut` stuck at true after recovery (M8).
    warningEmittedRef.current = false;
  }, [phrasesKey, isError]);

  // H1 — bar fill animation. Seed to 0 on mount / phrases-swap, then RAF to
  // 100 so the CSS transition runs over `safeSeconds`. On isComplete, snap
  // to 100 in motion-quick. On isError, freeze where we are so the fade-out
  // shows the progress reached when the error happened.
  React.useEffect(() => {
    if (isError) return;
    if (isComplete) {
      setBarWidth(100);
      return;
    }
    setBarWidth(0);
    const raf = requestAnimationFrame(() => setBarWidth(100));
    return () => cancelAnimationFrame(raf);
  }, [phrasesKey, isComplete, isError]);

  // Chained setTimeout for phrase advancement — prefer over setInterval to
  // avoid drift on throttled tabs and mobile (Story 2.8 §4.2).
  //
  // H2 — seed local `index` from the current `phraseIndexRef` so a mid-flight
  // dep change (caller revises `estimatedSeconds`) RESUMES from the current
  // phrase instead of restarting at 0. The previous closure-local `let index
  // = 0` jumped users BACKWARDS, violating the anti-cirque invariant.
  React.useEffect(() => {
    if (safePhrases.length <= 1) return;
    if (isComplete || isError) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let index = phraseIndexRef.current;
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
      // M7 — re-check at firing time: a completion/error landing on the same
      // tick as this timer would otherwise leak a false "exceeded" event.
      if (completedEmittedRef.current || erroredEmittedRef.current) return;
      setShowWarning(true);
      if (!warningEmittedRef.current) {
        warningEmittedRef.current = true;
        const startedAt = startedAtRef.current ?? Date.now();
        track({
          name: "scenario_loader_estimation_exceeded",
          context,
          estimated_seconds: safeSeconds,
          // M6 — true wall-clock elapsed, not the estimate. Under throttled
          // tabs / mobile background-timer slippage the two diverge by
          // several seconds — using the estimate hid real OCR overruns.
          actual_seconds_at_warning: (Date.now() - startedAt) / 1000,
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
  //
  // H4 — `phrasesKey` intentionally NOT in deps: a phrases-swap during an
  // active error state must not retrigger this effect (it would re-emit a
  // duplicate `scenario_loader_errored` because the start-stamp effect's
  // !isError gate keeps `erroredEmittedRef` true through the swap).
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
  }, [isError, context]);

  // M8 — in-place error recovery: when isError transitions back to false
  // (transient network blip followed by automatic retry without unmount),
  // reverse the fade-out and re-arm the emission latch so a subsequent
  // error re-emits analytics correctly.
  React.useEffect(() => {
    if (isError) return;
    if (!erroredEmittedRef.current) return;
    setIsFadingOut(false);
    erroredEmittedRef.current = false;
  }, [isError]);

  const { icon: Icon, srLabel } = CONTEXT_MAP[context];
  const particleAnimating = !isComplete && !isError;
  const dataState = isError
    ? "error"
    : isComplete
      ? "complete"
      : showWarning
        ? "warning"
        : "running";

  return (
    <>
      {/* Pass 2 PR2 — the final-state announcer (after </section>) is a
          SIBLING of the running-state region, not a descendant. AC6 spells
          out "une seconde zone `aria-live` SÉPARÉE". Two live regions
          nested inside each other (the section's `role="status"` implies
          polite + the inner span's `aria-live="polite"`) caused
          double-announcements on NVDA/JAWS in Pass 1 review. */}
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
        {/* M5 — particle stays MOUNTED (anti-cirque). On isComplete / isError,
            data-animating="false" pauses the keyframe in place via the Tailwind
            `animation-play-state: paused` utility — "stoppe sur sa frame
            visible" (AC3), not a brutal DOM removal. Reduced-motion still
            unmounts since the keyframe never starts. */}
        {!prefersReducedMotion ? (
          <span
            aria-hidden
            data-testid="scenario-loader-particle"
            data-animating={particleAnimating}
            className={cn(
              "absolute right-0 top-0 h-[10px] w-[10px] animate-scenario-loader-particle rounded-full bg-brand",
              !particleAnimating && "[animation-play-state:paused]",
            )}
          />
        ) : null}
      </div>

      {/* H3 (Pass 2 PR1) — crossfade via CSS grid stack: every `<p>` shares
          the same grid cell (col-start-1 row-start-1) so the container
          auto-sizes to the TALLEST phrase. The previous absolute-positioned
          stack capped the height at `min-h-7` (28 px) and let multi-line
          phrases (e.g. lycée variant "Qu'est-ce qui te plaît, vraiment ?"
          on a 375 px mobile) overflow into the progress bar below. Grid
          stack keeps the crossfade overlap (both `<p>` mounted with
          opacity transition) without breaking layout. */}
      <div className="grid w-full">
        {safePhrases.map((phrase, idx) => (
          <p
            key={idx}
            data-testid={idx === phraseIndex ? "scenario-loader-phrase" : undefined}
            aria-hidden={idx !== phraseIndex}
            className={cn(
              "col-start-1 row-start-1 text-center text-h2 font-semibold text-text",
              "transition-opacity duration-quick ease-standard",
              idx === phraseIndex ? "opacity-100" : "opacity-0",
            )}
          >
            {phrase}
          </p>
        ))}
      </div>

      <div className="flex w-full max-w-[280px] flex-col gap-3">
        <div
          aria-hidden
          className="h-1 w-full overflow-hidden rounded-full bg-bg-3"
          data-testid="scenario-loader-bar"
        >
          <div
            className="h-full rounded-full bg-brand"
            style={{
              // H1 — width is now driven by `barWidth` STATE seeded to 0 on
              // mount and RAF'd to 100 in the bar-animation effect, so the
              // CSS transition over `safeSeconds` actually runs. The old
              // `isComplete ? 100 : 0` left the bar empty for the full wait.
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
      </section>
      {/* Final-state announcer — sibling of the section, NOT a descendant.
          Empty `role="status"` (implicit) container that only ever holds
          the completion/error string; SRs read each transient state
          exactly once without double-counting through the section's own
          live region. */}
      <span aria-live="polite" className="sr-only">
        {isComplete && !isError ? "Terminé." : ""}
        {isError ? "Un problème est survenu, options disponibles ci-dessous." : ""}
      </span>
    </>
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
    <div
      className="flex animate-scenario-warning-in flex-col items-center gap-2"
      data-testid="scenario-loader-warning"
    >
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
