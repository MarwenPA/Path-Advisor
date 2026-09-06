/**
 * API client for early-outreach requests — Stories 5.4 + 5.5 + 5.7.
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

export type OutreachResponseAction = "interested" | "not_aligned" | "interview_requested";

export interface OutreachResponse {
  action: OutreachResponseAction;
  comment: string;
  proposed_slots: string[];
  accepted_slot: string;
  alternative_note: string;
  created_at: string;
}

export interface EarlyOutreachRequestItem {
  id: string;
  school_name: string;
  profession_name: string;
  status: EarlyOutreachRequestStatusValue;
  rejection_reason: string;
  response: OutreachResponse | null;
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

/** Story 5.7 — student accepts one of the school's proposed interview slots. */
export async function acceptInterviewSlot(
  outreachId: string,
  slot: string,
): Promise<EarlyOutreachRequestItem> {
  return apiFetch<EarlyOutreachRequestItem>(
    `/api/v1/outreach/requests/${encodeURIComponent(outreachId)}/interview/accept/`,
    { method: "POST", body: { slot }, csrfToken: readCsrfCookie() ?? undefined },
  );
}

/** Story 5.7 — student can't make any proposed slot, suggests one instead. */
export async function proposeInterviewAlternative(
  outreachId: string,
  note: string,
): Promise<EarlyOutreachRequestItem> {
  return apiFetch<EarlyOutreachRequestItem>(
    `/api/v1/outreach/requests/${encodeURIComponent(outreachId)}/interview/alternative/`,
    { method: "POST", body: { note }, csrfToken: readCsrfCookie() ?? undefined },
  );
}
