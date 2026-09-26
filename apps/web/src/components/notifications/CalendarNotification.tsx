/**
 * `CalendarNotification` — Story 8.7, UX-DR17 + UX-DR28.
 *
 * THE reusable renderer for anything pinned to the Parcoursup calendar:
 * factual title, calm description, a NON-BLOCKING checklist of suggested
 * preparations, one calm CTA. Currently consumed by the DeltaRecap
 * interstitial (8.6, card kind `parcoursup_milestone`); any future
 * calendar screen reuses it as-is.
 *
 * "Le même composant alimente email et app" (AC3) resolves to a single
 * COPY source + data shape, not a single code module: every sentence
 * comes from `apps/api/.../milestone_copy.py::MILESTONE_COPY` (where the
 * 8.3 tone lint constrains it) through the 8.6 card shape
 * `{title, body, days_until, recommended_actions[], cta}`. The Django
 * email template (8.3) and this component are the two rendering layers.
 * This component writes NO sentence of its own.
 *
 * Anti-countdown (AC1, tested): the "dans X jours" badge is STATIC muted
 * text — no timer, no `setInterval`, no `aria-live`, no red. Time-left is
 * information here, never pressure.
 */

import Link from "next/link";

export interface CalendarNotificationProps {
  /** Factual title, backend-built (e.g. « Parcoursup : la plateforme ouvre le 14 octobre 2026 »). */
  jalon: string;
  daysUntil: number;
  /** Calm intro, backend-built. */
  body: string;
  /** Non-blocking suggestions — rendered as a plain list, never checkboxes. */
  recommendedActions: string[];
  ctaLabel: string;
  ctaUrl: string;
  /** Optional side effect on CTA click (e.g. DeltaRecap's ack). */
  onCtaClick?: () => void;
}

export function CalendarNotification({
  jalon,
  daysUntil,
  body,
  recommendedActions,
  ctaLabel,
  ctaUrl,
  onCtaClick,
}: CalendarNotificationProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline gap-2">
        <h2 className="text-xl font-semibold text-foreground">{jalon}</h2>
        <span data-testid="calendar-days-until" className="text-sm text-muted-foreground">
          {daysUntil === 0 ? "aujourd'hui" : `dans ${daysUntil} jour${daysUntil > 1 ? "s" : ""}`}
        </span>
      </div>
      <p className="text-muted-foreground">{body}</p>
      {recommendedActions.length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          {recommendedActions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      ) : null}
      <Link
        href={ctaUrl}
        onClick={onCtaClick}
        className="inline-block w-fit rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        {ctaLabel}
      </Link>
    </div>
  );
}
