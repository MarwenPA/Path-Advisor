/**
 * API fetchers for the DeltaRecap interstitial — Story 8.6.
 *
 * Mirrors `apps/api/apps/notifications/views.py`:
 *   - `GET /api/v1/me/delta-recap/` — the "what moved since your last
 *     visit" cards. ALL copy (title/body/CTA labels) is built server-side
 *     so the calm-tone lint stays executable in Python; this client never
 *     fabricates a sentence.
 *   - `POST /api/v1/me/delta-recap/ack/` — moves the cursor. Fired by
 *     "Tout vu, continuer" AND by any card CTA click (navigating through
 *     a card = having seen the recap). GET never moves the cursor.
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type DeltaRecapCardKind = "school_response" | "new_schools" | "parcoursup_milestone";

export interface DeltaRecapCard {
  kind: DeltaRecapCardKind;
  title: string;
  body: string;
  cta_label: string;
  /** App-relative route (e.g. `/mes-envois/eor_x`) — pushed via next/link. */
  cta_url: string;
  /** 5.8's before/after admission stat — null when no delta was applied. */
  stat_before: number | null;
  stat_after: number | null;
  /** `new_schools` only. */
  count?: number;
  /** `parcoursup_milestone` only (8.7's CalendarNotification shape). */
  days_until?: number;
  recommended_actions?: string[];
}

export interface DeltaRecapResponse {
  cards: DeltaRecapCard[];
}

export async function fetchDeltaRecap(): Promise<DeltaRecapResponse> {
  return apiFetch<DeltaRecapResponse>("/api/v1/me/delta-recap/");
}

export async function acknowledgeDeltaRecap(): Promise<void> {
  return apiFetch<void>("/api/v1/me/delta-recap/ack/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}
