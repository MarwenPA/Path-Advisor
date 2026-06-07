/**
 * MFA API client — Story 1.6.
 *
 * The 5 MFA endpoints split in two groups:
 *
 * 1. **Public (no session cookie, `mfa_session` is the auth proof):**
 *    - `mfaEnrollStart`   — POST /api/v1/auth/mfa/enroll/start/
 *    - `mfaEnrollConfirm` — POST /api/v1/auth/mfa/enroll/confirm/
 *    - `mfaChallenge`     — POST /api/v1/auth/mfa/challenge/
 *
 * 2. **Auth-required (session cookie + step-up password+TOTP re-auth):**
 *    - `mfaDisable`                 — POST /api/v1/auth/mfa/disable/
 *    - `mfaRegenerateRecoveryCodes` — POST /api/v1/auth/mfa/recovery-codes/regenerate/
 *
 * The `mfa_session` token is opaque from the client's POV — it's a
 * server-signed string with 5-min TTL, IP-bound, single-use. The frontend
 * stores it in `sessionStorage` (NOT `localStorage` — never persisted
 * across tabs / page reloads beyond the MFA flow) and passes it back.
 */

import { apiFetch, readCsrfCookie } from "./client";
import { fetchCsrfToken, type CurrentUser } from "./auth";

// ---------------------------------------------------------------------------
// Public endpoints — driven by mfa_session
// ---------------------------------------------------------------------------

export interface MfaEnrollStartResponse {
  otpauth_url: string;
  qr_svg: string;
  issuer: string;
  account_label: string;
}

export async function mfaEnrollStart(
  mfaSession: string,
): Promise<MfaEnrollStartResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<MfaEnrollStartResponse>("/api/v1/auth/mfa/enroll/start/", {
    method: "POST",
    body: { mfa_session: mfaSession },
    csrfToken,
  });
}

export interface MfaEnrollConfirmResponse {
  recovery_codes: string[];
  user: CurrentUser;
}

export async function mfaEnrollConfirm(
  mfaSession: string,
  code: string,
): Promise<MfaEnrollConfirmResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<MfaEnrollConfirmResponse>("/api/v1/auth/mfa/enroll/confirm/", {
    method: "POST",
    body: { mfa_session: mfaSession, code },
    csrfToken,
  });
}

export interface MfaChallengeResponse {
  user: CurrentUser;
}

export type MfaChallengeMethod = "totp" | "recovery";

export async function mfaChallenge(
  mfaSession: string,
  code: string,
  method: MfaChallengeMethod = "totp",
): Promise<MfaChallengeResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<MfaChallengeResponse>("/api/v1/auth/mfa/challenge/", {
    method: "POST",
    body: { mfa_session: mfaSession, code, method },
    csrfToken,
  });
}

// ---------------------------------------------------------------------------
// Auth-required endpoints — session + step-up password+code
// ---------------------------------------------------------------------------

export interface MfaReauthPayload {
  password: string;
  /** 6-digit TOTP — recovery codes are NOT accepted (code-review D4). */
  code: string;
}

export interface MfaEnrollStartFromSessionResponse {
  mfa_session: string;
  mfa_enrollment_required: true;
}

/**
 * In-place enrollment start for an already-authenticated B2C user
 * (code-review D3). Replaces the prior logout-and-re-login flow. Returns
 * a fresh `mfa_session` (stage=`mfa_enrollment_pending`) that the caller
 * stores in sessionStorage before routing to `/auth/mfa/enroll`.
 */
export async function mfaEnrollStartFromSession(): Promise<MfaEnrollStartFromSessionResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<MfaEnrollStartFromSessionResponse>(
    "/api/v1/auth/mfa/enroll/start-from-session/",
    { method: "POST", csrfToken },
  );
}

export async function mfaDisable(
  payload: MfaReauthPayload,
): Promise<{ detail: string }> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<{ detail: string }>("/api/v1/auth/mfa/disable/", {
    method: "POST",
    body: payload,
    csrfToken,
  });
}

export interface MfaRegenerateRecoveryResponse {
  recovery_codes: string[];
}

export async function mfaRegenerateRecoveryCodes(
  payload: MfaReauthPayload,
): Promise<MfaRegenerateRecoveryResponse> {
  const csrfToken = readCsrfCookie() ?? (await fetchCsrfToken());
  return apiFetch<MfaRegenerateRecoveryResponse>(
    "/api/v1/auth/mfa/recovery-codes/regenerate/",
    {
      method: "POST",
      body: payload,
      csrfToken,
    },
  );
}

// ---------------------------------------------------------------------------
// sessionStorage helpers — the mfa_session lives here for the duration of
// the MFA flow (login → enroll/challenge). Cleared on any leave.
// ---------------------------------------------------------------------------

const MFA_SESSION_STORAGE_KEY = "path-advisor:mfa-session";

/**
 * Store the mfa_session token in sessionStorage with defensive try/catch
 * (code-review P19): Safari private mode + locked-down corporate browsers
 * throw `SecurityError` / `QuotaExceededError` on `setItem`. Without the
 * catch, the login flow crashes mid-route. Returns `true` on success so
 * the caller can fall back to in-memory state on failure.
 */
export function storeMfaSession(token: string): boolean {
  if (typeof window === "undefined") return false;
  try {
    window.sessionStorage.setItem(MFA_SESSION_STORAGE_KEY, token);
    return true;
  } catch {
    return false;
  }
}

export function readMfaSession(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(MFA_SESSION_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function clearMfaSession(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(MFA_SESSION_STORAGE_KEY);
  } catch {
    /* sessionStorage blocked — already not stored, nothing to clear */
  }
}
