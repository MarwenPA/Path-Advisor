"use client";

import * as React from "react";
import {
  ArrowRight,
  CreditCard,
  FileQuestion,
  HelpCircle,
  Loader2,
  Pencil,
  RotateCw,
  Send,
  WifiOff,
  type LucideIcon,
} from "lucide-react";

import {
  track,
  type GracefulFallbackContext as AnalyticsGracefulFallbackContext,
} from "@/lib/analytics/events";
import { cn } from "@/lib/utils";

/*
 * GracefulFallback — Couche 3 Path-Advisor primitive (Story 2.9).
 *
 * Renders a calm, non-dead-end recovery screen. Two equally-weighted CTAs
 * (primary + secondary) plus an optional discreet tertiary link.
 *
 * Design invariants (Story 2.9 §4.4):
 *   - No red / no danger color anywhere — color-text-muted on the icon is
 *     enough of a signal. The TITLE carries the gravity, not the design.
 *   - The two primary CTAs are STRICTLY equivalent in shape (height, padding,
 *     font-weight, radius) — only background / border / text-color differ.
 *     Anti-dark-pattern: visual weight should never nudge toward an option.
 *   - Inline by default — no modal, no overlay. Consumers that need modal
 *     framing compose `<Dialog><GracefulFallback /></Dialog>` themselves.
 *   - No default copy — the caller MUST supply `title` and `description`.
 *     The dev-only `console.warn` is a guard-rail, not a copyright.
 */

export type GracefulFallbackContext = AnalyticsGracefulFallbackContext;

export type GracefulFallbackActionIcon = "arrow-right" | "rotate" | "pencil" | "none";

export type GracefulFallbackAction = {
  label: string;
  onClick: () => void | Promise<void>;
  icon?: GracefulFallbackActionIcon;
  isDisabled?: boolean;
  isSubmitting?: boolean;
};

export type GracefulFallbackProps = {
  title: string;
  description: string;
  context?: GracefulFallbackContext;
  primaryAction: GracefulFallbackAction;
  secondaryAction: GracefulFallbackAction;
  tertiaryLink?: GracefulFallbackAction;
  /** Override the default Lucide illustration. The provided node is rendered
   *  inside the 96×96 circle and inherits `text-muted`. */
  iconOverride?: React.ReactNode;
};

const CONTEXT_ICON: Record<GracefulFallbackContext, LucideIcon> = {
  ocr: FileQuestion,
  payment: CreditCard,
  school_send: Send,
  network: WifiOff,
  generic: HelpCircle,
};

const ACTION_ICON: Record<Exclude<GracefulFallbackActionIcon, "none">, LucideIcon> = {
  "arrow-right": ArrowRight,
  rotate: RotateCw,
  pencil: Pencil,
};

const FORBIDDEN_TITLE_WORDS = [
  "erreur",
  "Erreur",
  "ERREUR",
  "échec",
  "impossible",
  "incapable",
  "raté",
];

function validateTitleInDev(title: string): void {
  if (process.env.NODE_ENV === "production") return;
  const trimmed = title.trim();
  if (trimmed.length === 0) {
    throw new Error("[GracefulFallback] `title` cannot be empty");
  }
  if (trimmed.startsWith("Tu ")) {
    console.warn(
      "[GracefulFallback] title viole le principe émotionnel dignité (agentivité utilisateur). Story 2.9 AC1.",
    );
    return;
  }
  for (const word of FORBIDDEN_TITLE_WORDS) {
    if (title.includes(word)) {
      console.warn(
        `[GracefulFallback] title contient un mot proscrit ("${word}"). Story 2.9 AC1.`,
      );
      return;
    }
  }
  if (title.length > 80) {
    console.warn("[GracefulFallback] title > 80 caractères — envisager de simplifier.");
  }
}

// Shared shape between primary and secondary buttons — only colors diverge.
// The test in `graceful-fallback.test.tsx` asserts that both buttons contain
// every class in this list, which is the rampart against future drift toward
// a dark pattern (Story 2.9 AC3).
const SHARED_CTA_SHAPE =
  "inline-flex h-12 w-full items-center justify-center gap-2 rounded-md px-4 text-base font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed";

// M13 (post-review patch) — Story 2.9 AC3 specifies primary text = #FFFFFF.
// `text-primary-foreground` resolved to `--color-bg` (#FAFAF7, the off-white
// app background) which carried a slightly lower contrast against
// `--color-brand`. `text-white` is pure white and is contrast-safe on every
// brand-shade variant we ship.
const PRIMARY_COLORS =
  "bg-brand border border-brand text-white hover:bg-brand-hover hover:border-brand-hover";
const SECONDARY_COLORS =
  "bg-transparent border border-border-strong text-text hover:bg-bg-2";

function ActionIcon({
  icon,
  isSubmitting,
}: {
  icon: GracefulFallbackActionIcon | undefined;
  isSubmitting: boolean;
}) {
  if (isSubmitting) {
    return <Loader2 className="h-4 w-4 animate-spin" aria-hidden />;
  }
  if (!icon || icon === "none") return null;
  const Icon = ACTION_ICON[icon];
  return <Icon className="h-[18px] w-[18px]" aria-hidden />;
}

export function GracefulFallback({
  title,
  description,
  context = "generic",
  primaryAction,
  secondaryAction,
  tertiaryLink,
  iconOverride,
}: GracefulFallbackProps) {
  validateTitleInDev(title);

  const titleId = React.useId();
  const regionRef = React.useRef<HTMLElement>(null);
  const primaryRef = React.useRef<HTMLButtonElement>(null);
  const secondaryRef = React.useRef<HTMLButtonElement>(null);
  const tertiaryRef = React.useRef<HTMLButtonElement>(null);
  const shownAtRef = React.useRef<number | null>(null);
  const shownEmittedRef = React.useRef(false);

  const Icon = CONTEXT_ICON[context];

  React.useEffect(() => {
    if (shownEmittedRef.current) return;
    shownEmittedRef.current = true;
    shownAtRef.current = Date.now();
    track({
      name: "graceful_fallback_shown",
      context,
      title,
      has_tertiary: Boolean(tertiaryLink),
    });
  }, [context, title, tertiaryLink]);

  // Take focus only if the page hasn't placed it elsewhere already.
  //
  // M9 (post-review patch) — fall through primary → secondary → tertiary →
  // region when the higher-priority target is disabled (browsers no-op
  // `.focus()` on `<button disabled>`, dropping SR users at the top of the
  // page). The region carries `tabIndex={-1}` for the final fallback so
  // screen readers still land on the recovery section's accessible name.
  React.useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.activeElement && document.activeElement !== document.body) return;
    const targets = [
      !primaryAction.isDisabled ? primaryRef.current : null,
      !secondaryAction.isDisabled ? secondaryRef.current : null,
      tertiaryLink && !tertiaryLink.isDisabled ? tertiaryRef.current : null,
      regionRef.current,
    ];
    for (const target of targets) {
      if (!target) continue;
      target.focus();
      if (document.activeElement === target) return;
    }
  }, [primaryAction.isDisabled, secondaryAction.isDisabled, tertiaryLink]);

  const secondsSinceShown = () =>
    (Date.now() - (shownAtRef.current ?? Date.now())) / 1000;

  const handleClick = (
    action: GracefulFallbackAction,
    role: "primary" | "secondary" | "tertiary",
  ) => {
    if (action.isDisabled || action.isSubmitting) return;
    if (role === "primary") {
      track({
        name: "graceful_fallback_primary_clicked",
        context,
        primary_label: action.label,
        seconds_since_shown: secondsSinceShown(),
      });
    } else if (role === "secondary") {
      track({
        name: "graceful_fallback_secondary_clicked",
        context,
        secondary_label: action.label,
        seconds_since_shown: secondsSinceShown(),
      });
    } else {
      track({
        name: "graceful_fallback_tertiary_clicked",
        context,
        tertiary_label: action.label,
        seconds_since_shown: secondsSinceShown(),
      });
    }
    // M14 (post-review patch) — call synchronously so sync handlers run
    // before this function returns (tests rely on this contract). If the
    // result is a thenable, attach a catch so a rejected Promise doesn't
    // surface as a global `unhandledrejection` event. Callers that want to
    // react to failures should handle them inside `onClick` themselves.
    const maybePromise = action.onClick();
    if (maybePromise && typeof (maybePromise as Promise<void>).then === "function") {
      (maybePromise as Promise<void>).catch(() => {
        /* swallowed — recovery surface is already the fallback */
      });
    }
  };

  return (
    <section
      ref={regionRef}
      role="region"
      aria-labelledby={titleId}
      data-context={context}
      // L1 (post-review patch) — Story 2.9 AC2 specifies vertical padding
      // `space-6` (24 px) on mobile, `space-12` (48 px) on desktop. The
      // previous `py-12` always shipped the desktop value on mobile too.
      // tabIndex={-1} so the M9 focus-fallthrough can land here when every
      // CTA is disabled.
      tabIndex={-1}
      className="mx-auto flex w-full max-w-[600px] flex-col px-6 py-6 sm:px-12 sm:py-12"
    >
      <div
        aria-hidden
        className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full border border-border bg-bg-2"
        data-testid={`fallback-icon-${context}`}
      >
        {iconOverride ?? <Icon className="h-10 w-10 text-text-muted" aria-hidden />}
      </div>

      <h2
        id={titleId}
        className="mb-3 text-center text-h2 font-semibold text-text md:text-h2-desktop"
      >
        {title}
      </h2>

      {description ? (
        <p className="mb-8 text-center text-body text-text-muted">{description}</p>
      ) : null}

      <div
        role="group"
        aria-label="Options disponibles"
        className="mb-6 flex flex-col gap-3"
      >
        <button
          ref={primaryRef}
          type="button"
          onClick={() => handleClick(primaryAction, "primary")}
          disabled={primaryAction.isDisabled}
          aria-disabled={primaryAction.isDisabled || undefined}
          aria-busy={primaryAction.isSubmitting || undefined}
          data-action="primary"
          className={cn(
            SHARED_CTA_SHAPE,
            PRIMARY_COLORS,
            (primaryAction.isDisabled || primaryAction.isSubmitting) && "opacity-60",
            primaryAction.isSubmitting && "cursor-wait",
          )}
        >
          <span>{primaryAction.label}</span>
          <ActionIcon
            icon={primaryAction.icon}
            isSubmitting={Boolean(primaryAction.isSubmitting)}
          />
        </button>
        <button
          ref={secondaryRef}
          type="button"
          onClick={() => handleClick(secondaryAction, "secondary")}
          disabled={secondaryAction.isDisabled}
          aria-disabled={secondaryAction.isDisabled || undefined}
          aria-busy={secondaryAction.isSubmitting || undefined}
          data-action="secondary"
          className={cn(
            SHARED_CTA_SHAPE,
            SECONDARY_COLORS,
            (secondaryAction.isDisabled || secondaryAction.isSubmitting) && "opacity-60",
            secondaryAction.isSubmitting && "cursor-wait",
          )}
        >
          <span>{secondaryAction.label}</span>
          <ActionIcon
            icon={secondaryAction.icon}
            isSubmitting={Boolean(secondaryAction.isSubmitting)}
          />
        </button>
      </div>

      <span aria-live="polite" className="sr-only">
        {primaryAction.isSubmitting || secondaryAction.isSubmitting ? "Action en cours." : ""}
      </span>

      {tertiaryLink ? (
        <button
          ref={tertiaryRef}
          type="button"
          onClick={() => handleClick(tertiaryLink, "tertiary")}
          disabled={tertiaryLink.isDisabled}
          data-action="tertiary"
          className="mx-auto inline-flex min-h-11 items-center justify-center px-3 py-2 text-body-sm font-medium text-brand underline underline-offset-4 hover:text-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {tertiaryLink.label}
        </button>
      ) : null}
    </section>
  );
}

export default GracefulFallback;
