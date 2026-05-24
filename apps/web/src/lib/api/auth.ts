/**
 * Auth API surface (Story 1.3 — student ≥ 15 signup + email verification).
 *
 * Keeps the front-end ergonomics narrow: feature components import these
 * functions, never `apiFetch` directly. JSON shapes mirror the Django payload
 * (`snake_case` end-to-end — no camelCase conversion).
 */

import { apiFetch, readCsrfCookie } from "./client";

export interface SignupPayload {
  email: string;
  password1: string;
  password2: string;
  birth_date: string; // ISO YYYY-MM-DD
  consent_rgpd_accepted: boolean;
  consent_cgu_version: string;
  /** Required when the student is < 15 years old (Story 1.4). */
  parent_email?: string;
}

export interface CsrfResponse {
  csrf_token: string;
}

export interface SignupResponse {
  detail?: string;
  // dj-rest-auth returns nothing useful beyond `detail` when the user is unverified;
  // when verification is disabled the user object lands here. Story 1.3 keeps mandatory
  // verification, so the only field consistently present is `detail`.
}

export interface VerifyEmailResponse {
  detail: string;
}

/** Seed the `csrftoken` cookie + return the token value for the next mutation. */
export async function fetchCsrfToken(): Promise<string> {
  const { csrf_token } = await apiFetch<CsrfResponse>("/api/v1/auth/csrf/");
  return csrf_token;
}

export async function signupStudent(payload: SignupPayload): Promise<SignupResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<SignupResponse>("/api/v1/auth/registration/", {
    method: "POST",
    body: payload,
    csrfToken,
  });
}

export async function verifyEmail(key: string): Promise<VerifyEmailResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<VerifyEmailResponse>("/api/v1/auth/registration/verify-email/", {
    method: "POST",
    body: { key },
    csrfToken,
  });
}

export async function resendVerificationEmail(email: string): Promise<{ detail: string }> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<{ detail: string }>("/api/v1/auth/registration/resend-email/", {
    method: "POST",
    body: { email },
    csrfToken,
  });
}

/** CGU/RGPD version currently in force — bump this string when the policy changes. */
export const CGU_RGPD_VERSION = "2026-05-15";

// --- Story 1.4 — Parental consent flow --------------------------------------

export interface CurrentUser {
  id: string;
  email: string;
  role: string;
  status: string;
  is_fully_active: boolean;
}

/**
 * Fetch the authenticated user. Throws ApiError on 401/403 — the caller decides
 * whether to redirect to /auth/login or surface the error.
 */
export async function fetchCurrentUser(): Promise<CurrentUser> {
  return apiFetch<CurrentUser>("/api/v1/auth/user/");
}

export interface ParentalConsentStatus {
  student_email_masked: string;
  child_age: number;
  requested_at: string;
  expires_at: string;
  status: "pending" | "granted" | "refused" | "expired";
}

export interface ParentalConsentDecisionPayload {
  decision: "granted" | "refused";
  content_hash: string; // 64-char hex SHA-256 from ConsentDialog
  accepted_at: string; // ISO 8601
}

export interface ParentalConsentDecisionResponse {
  decision: "granted" | "refused";
  child_status: string;
}

export async function fetchParentalConsentStatus(token: string): Promise<ParentalConsentStatus> {
  return apiFetch<ParentalConsentStatus>(
    `/api/v1/auth/parental-consent/${encodeURIComponent(token)}/`,
  );
}

export async function decideParentalConsent(
  token: string,
  payload: ParentalConsentDecisionPayload,
): Promise<ParentalConsentDecisionResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<ParentalConsentDecisionResponse>(
    `/api/v1/auth/parental-consent/${encodeURIComponent(token)}/decide/`,
    {
      method: "POST",
      body: payload,
      csrfToken,
    },
  );
}

export async function resendParentalConsentEmail(): Promise<{ detail: string }> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<{ detail: string }>("/api/v1/auth/parental-consent/resend/", {
    method: "POST",
    csrfToken,
  });
}
