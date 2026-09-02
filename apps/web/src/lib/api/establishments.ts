/**
 * Establishments API client — Story 6.5 §T7 (minimal frontend).
 *
 * Only the two public accept flows are wired here — the admin endpoints
 * (create establishment/cohort/counselor invitation, CSV import) are API
 * only for this story (§6 Out of Scope: back-office UI is Epic 9).
 */
import { apiFetch } from "@/lib/api/client";

export interface CounselorInvitationPublicStatus {
  establishment_name: string;
  email: string;
  status: "pending" | "accepted" | "expired";
}

export interface StudentInvitationPublicStatus {
  establishment_name: string;
  status: "pending" | "accepted" | "expired";
}

export async function fetchCounselorInvitationStatus(
  token: string,
): Promise<CounselorInvitationPublicStatus> {
  return apiFetch<CounselorInvitationPublicStatus>(
    `/api/v1/auth/counselor-invitation/${encodeURIComponent(token)}/`,
  );
}

export async function acceptCounselorInvitation(
  token: string,
  password: string,
): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>(
    `/api/v1/auth/counselor-invitation/${encodeURIComponent(token)}/accept/`,
    { method: "POST", body: { password } },
  );
}

export async function fetchStudentInvitationStatus(
  token: string,
): Promise<StudentInvitationPublicStatus> {
  return apiFetch<StudentInvitationPublicStatus>(
    `/api/v1/students/invitation/${encodeURIComponent(token)}/`,
  );
}

export async function acceptStudentInvitation(
  token: string,
  password: string,
): Promise<{ detail: string; status: string }> {
  return apiFetch<{ detail: string; status: string }>(
    `/api/v1/students/invitation/${encodeURIComponent(token)}/accept/`,
    { method: "POST", body: { password } },
  );
}
