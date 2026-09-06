/**
 * API client for early-outreach requests — Stories 5.4 + 5.5.
 */
import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface OutreachQuota {
  used: number;
  limit: number;
  remaining: number;
}

export type EarlyOutreachRequestStatusValue =
  | "pending"
  | "pending_moderation"
  | "rejected"
  | "responded"
  | "expired_7d";

export interface EarlyOutreachRequestItem {
  id: string;
  school_name: string;
  profession_name: string;
  status: EarlyOutreachRequestStatusValue;
  rejection_reason: string;
  created_at: string;
}

export interface PaginatedOutreachRequests {
  count: number;
  next: string | null;
  previous: string | null;
  results: EarlyOutreachRequestItem[];
}

/** AC1/AC3 — read-only, no side effect: lets the front decide button-vs-quota-message. */
export async function fetchOutreachQuota(): Promise<OutreachQuota> {
  return apiFetch<OutreachQuota>("/api/v1/outreach/quota/");
}

/** AC4 — student-scoped list for `/mes-envois`. */
export async function fetchOutreachRequests(): Promise<PaginatedOutreachRequests> {
  return apiFetch<PaginatedOutreachRequests>("/api/v1/outreach/requests/");
}

/** AC2/AC5 — create. `parcours` is resolved server-side, never sent from here. */
export async function createOutreachRequest(
  schoolSlug: string,
  payload: { profession_id: string; motivation_text?: string },
): Promise<EarlyOutreachRequestItem> {
  return apiFetch<EarlyOutreachRequestItem>(
    `/api/v1/schools/${encodeURIComponent(schoolSlug)}/outreach/`,
    { method: "POST", body: payload, csrfToken: readCsrfCookie() ?? undefined },
  );
}

/** Story 5.5 — student corrects+resubmits a `rejected` motivation. */
export async function resubmitOutreachRequest(
  outreachId: string,
  motivationText: string,
): Promise<EarlyOutreachRequestItem> {
  return apiFetch<EarlyOutreachRequestItem>(
    `/api/v1/outreach/requests/${encodeURIComponent(outreachId)}/resubmit/`,
    {
      method: "POST",
      body: { motivation_text: motivationText },
      csrfToken: readCsrfCookie() ?? undefined,
    },
  );
}
