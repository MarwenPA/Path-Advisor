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

export type UserRole =
  | "student"
  | "parent"
  | "counselor"
  | "school_admin"
  | "path_admin"
  // Story 1.7 §AC1 — 6th role per PRD §"Matrice RBAC". Support users
  // handle tickets with a masked profile view ; no audit log access.
  | "support";

export type UserStatus =
  | "email_unverified"
  | "pending_parental_consent"
  | "active"
  | "suspended"
  | "deleted";

export interface CurrentUser {
  id: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  is_fully_active: boolean;
  // Story 1.6 — MFA dashboard signals. `mfa_required_by_role` is the static
  // NFR-S2 flag (true for staff). `mfa_enrolled` is the actual state.
  // `mfa_recovery_codes_remaining` is the count of unused codes (the codes
  // themselves are NEVER returned outside the enrollment-confirm /
  // regenerate response).
  mfa_required_by_role: boolean;
  mfa_enrolled: boolean;
  mfa_recovery_codes_remaining: number;
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

// --- Story 1.5 — Login + logout + password reset ----------------------------

export interface LoginResponse {
  user: CurrentUser;
  // Story 1.6 — MFA branch. When `mfa_required` is true, the response body
  // does NOT come with a session cookie. The frontend stores `mfa_session`
  // in `sessionStorage` and routes to `/auth/mfa/enroll` (if
  // `mfa_enrollment_required`) or `/auth/mfa/challenge` (otherwise). The
  // challenge / enrollment-confirm endpoint completes the login and posts
  // the cookie.
  mfa_required?: boolean;
  mfa_enrollment_required?: boolean;
  mfa_session?: string;
}

export async function loginUser(email: string, password: string): Promise<LoginResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<LoginResponse>("/api/v1/auth/login/", {
    method: "POST",
    body: { email, password },
    csrfToken,
  });
}

export async function logoutUser(): Promise<{ detail: string }> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<{ detail: string }>("/api/v1/auth/logout/", {
    method: "POST",
    csrfToken,
  });
}

/**
 * Request a password-reset email. Always returns 200 — the body is identical
 * whether the email is registered or not (anti-enumeration per Story 1.5 §AC5).
 */
export async function requestPasswordReset(email: string): Promise<{ detail: string }> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<{ detail: string }>("/api/v1/auth/password/reset/", {
    method: "POST",
    body: { email },
    csrfToken,
  });
}

export interface ConfirmPasswordResetPayload {
  uid: string;
  token: string;
  new_password1: string;
  new_password2: string;
}

export async function confirmPasswordReset(
  payload: ConfirmPasswordResetPayload,
): Promise<{ detail: string }> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<{ detail: string }>("/api/v1/auth/password/reset/confirm/", {
    method: "POST",
    body: payload,
    csrfToken,
  });
}
