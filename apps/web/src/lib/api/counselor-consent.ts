/**
 * API client for the student-side counselor-consent flow — Story 6.7.
 */
import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface PendingCounselorConsent {
  id: string;
  counselor_email: string;
  status: "pending" | "granted" | "refused";
  requested_at: string;
  decided_at: string | null;
}

export async function fetchPendingCounselorConsents(): Promise<PendingCounselorConsent[]> {
  return apiFetch<PendingCounselorConsent[]>("/api/v1/establishments/consent-requests/");
}

export async function decideCounselorConsent(
  consentId: string,
  granted: boolean,
): Promise<PendingCounselorConsent> {
  return apiFetch<PendingCounselorConsent>(
    `/api/v1/establishments/consent-requests/${encodeURIComponent(consentId)}/decide/`,
    { method: "POST", body: { granted }, csrfToken: readCsrfCookie() ?? undefined },
  );
}
