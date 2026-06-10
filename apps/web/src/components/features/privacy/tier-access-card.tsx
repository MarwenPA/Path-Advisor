/**
 * <TierAccessCard> — one row in the Accès tiers list (Story 1.9 §AC4, §AC5).
 *
 * Server-renderable (no client state) ; the disabled "Révoquer" button
 * becomes active in Story 1.10 via a small Client Component island.
 * RGAA AA : the card is an <article> labeled by the display name + tier
 * badge ; the disabled button is `aria-describedby` the visibility list so
 * a screen-reader user knows WHAT they would revoke.
 */
import { RevokeAccessButton } from "@/components/features/privacy/revoke-access-button";
import { ACCESS_LIST_COPY, type DataAreaKey, type TierType } from "@/lib/i18n/fr/access-list";

import type { AccessListEntry } from "@/lib/api/access-list";

const RELATIVE_TIME = new Intl.RelativeTimeFormat("fr-FR", { numeric: "auto" });

function relativeFromNow(iso: string, now: Date = new Date()): string {
  const then = new Date(iso);
  const diffMs = then.getTime() - now.getTime();
  const diffMinutes = Math.round(diffMs / 60_000);
  if (Math.abs(diffMinutes) < 1) return "à l'instant";
  const minutes = Math.abs(diffMinutes);
  if (minutes < 60) return RELATIVE_TIME.format(diffMinutes, "minute");
  const diffHours = Math.round(diffMs / 3_600_000);
  if (Math.abs(diffHours) < 24) return RELATIVE_TIME.format(diffHours, "hour");
  const diffDays = Math.round(diffMs / 86_400_000);
  if (Math.abs(diffDays) < 7) return RELATIVE_TIME.format(diffDays, "day");
  const diffWeeks = Math.round(diffDays / 7);
  if (Math.abs(diffWeeks) < 5) return RELATIVE_TIME.format(diffWeeks, "week");
  const diffMonths = Math.round(diffDays / 30);
  if (Math.abs(diffMonths) < 12) return RELATIVE_TIME.format(diffMonths, "month");
  const diffYears = Math.round(diffDays / 365);
  return RELATIVE_TIME.format(diffYears, "year");
}

function dataAreaLabel(key: string): string {
  return (
    ACCESS_LIST_COPY.dataAreaLabels[key as DataAreaKey] ??
    /* fallback for unknown areas — should be impossible via the matrix test */ key
  );
}

const TIER_BADGE_CLASSES: Record<TierType, string> = {
  parent: "bg-blue-100 text-blue-900",
  school: "bg-purple-100 text-purple-900",
  counselor: "bg-green-100 text-green-900",
};

export function TierAccessCard({ entry }: { entry: AccessListEntry }) {
  const titleId = `tier-${entry.id.replace(/[^a-zA-Z0-9-]/g, "-")}`;
  const visibilityListId = `${titleId}-visibility`;
  const tierLabel = ACCESS_LIST_COPY.tierBadge[entry.tier_type] ?? entry.tier_type;
  const grantedAtAbsolute = new Date(entry.granted_at).toLocaleString("fr-FR");

  return (
    <article
      aria-labelledby={titleId}
      className="flex flex-col gap-4 rounded-lg border border-border bg-bg p-6 shadow-sm"
    >
      <header className="flex flex-col gap-2 md:flex-row md:items-baseline md:justify-between">
        <div className="flex items-center gap-3">
          <h3 id={titleId} className="text-h3 font-semibold text-text">
            {entry.display_name}
          </h3>
          <span
            className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${TIER_BADGE_CLASSES[entry.tier_type]}`}
            aria-label={`Type d'accès : ${tierLabel}`}
          >
            {tierLabel}
          </span>
        </div>
        <p className="text-xs text-text-subtle">
          {ACCESS_LIST_COPY.grantedAtLabel} :{" "}
          <time dateTime={entry.granted_at} title={grantedAtAbsolute}>
            {relativeFromNow(entry.granted_at)}
          </time>
        </p>
      </header>

      <div id={visibilityListId} className="grid gap-3 md:grid-cols-2">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {ACCESS_LIST_COPY.visibleSectionTitle}
          </h4>
          <ul className="mt-1 list-inside list-disc text-sm text-text">
            {entry.visible_data.map((area) => (
              <li key={area}>{dataAreaLabel(area)}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {ACCESS_LIST_COPY.maskedSectionTitle}
          </h4>
          <ul className="mt-1 list-inside list-disc text-sm text-text-subtle">
            {entry.masked_data.map((area) => (
              <li key={area}>{dataAreaLabel(area)}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="flex justify-end">
        <RevokeAccessButton entry={entry} />
      </div>
    </article>
  );
}
