/**
 * Family API client — Story 6.1 §T7.4.
 *
 * Mirrors the Django DTOs 1:1 (snake_case in transit). CSRF token is
 * required on every mutating call (Story 1.3 pattern) except the anonymous
 * `acceptInvitation` call made before the CSRF cookie may exist for this
 * visitor — same contract as `decideParentalConsent`.
 */
import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type ParentRelationship = "mere" | "pere" | "tuteur" | "autre";

export type ParentInvitationStatus = "pending" | "accepted" | "expired" | "revoked";

export interface ParentInvitation {
  id: string;
  parent_email: string;
  relationship: ParentRelationship | null;
  custom_message: string | null;
  status: ParentInvitationStatus;
  created_at: string;
  expires_at: string;
  accepted_at: string | null;
}

export interface CreateParentInvitationPayload {
  parent_email: string;
  relationship?: ParentRelationship;
  custom_message?: string;
}

export async function fetchParentInvitations(): Promise<ParentInvitation[]> {
  return apiFetch<ParentInvitation[]>("/api/v1/family/parent-invitations/");
}

export async function createParentInvitation(
  payload: CreateParentInvitationPayload,
): Promise<ParentInvitation> {
  return apiFetch<ParentInvitation>("/api/v1/family/parent-invitations/", {
    method: "POST",
    body: payload,
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export async function resendParentInvitation(invitationId: string): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>(
    `/api/v1/family/parent-invitations/${encodeURIComponent(invitationId)}/resend/`,
    {
      method: "POST",
      csrfToken: readCsrfCookie() ?? undefined,
    },
  );
}

export interface ParentInvitationPublicStatus {
  student_first_name: string;
  student_masked_email: string;
  parent_email: string;
  relationship: ParentRelationship | null;
  custom_message: string | null;
  status: ParentInvitationStatus;
}

export async function fetchInvitationByToken(token: string): Promise<ParentInvitationPublicStatus> {
  return apiFetch<ParentInvitationPublicStatus>(
    `/api/v1/family/parent-invitations/${encodeURIComponent(token)}/`,
  );
}

export interface AcceptInvitationPayload {
  email?: string;
  password?: string;
  first_name?: string;
  last_name?: string;
}

export async function acceptInvitation(
  token: string,
  payload: AcceptInvitationPayload,
): Promise<{ detail: string; role: string }> {
  return apiFetch<{ detail: string; role: string }>(
    `/api/v1/family/parent-invitations/${encodeURIComponent(token)}/accept/`,
    {
      method: "POST",
      body: payload,
      csrfToken: readCsrfCookie() ?? undefined,
    },
  );
}
