/**
 * Typed wrappers around `/api/v1/auth/[me/]account-deletion/*` (Story 1.12).
 *
 * Two surfaces:
 *   - Authenticated `POST /me/account-deletion/` + `GET /me/account-deletion/status/`
 *     — used by the Settings page's "Zone dangereuse" section.
 *   - Public `GET /account-deletion/<token>/` + `POST .../cancel/` — used by the
 *     email-link landing page (no auth — the token IS the auth for one click).
 *
 * Errors flow through the standard `ApiError` Problem Details path; the
 * `type` URI lets callers differentiate (e.g. invalid password vs expired
 * grace window) for tailored copy.
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface AccountDeletionRequest {
  id: string;
  requested_at: string;
  hard_delete_after: string;
  cancelled_at: string | null;
  hard_deleted_at: string | null;
}

export interface AccountDeletionPublicStatus {
  user_email_masked: string;
  requested_at: string;
  hard_delete_after: string;
  status:
    | "pending_hard_delete"
    | "cancelled"
    | "hard_deleted"
    | "expired";
}

export interface AccountDeletionRequestPayload {
  password: string;
  /** SHA-256 hex from the ConsentDialog (Story 1.14 §AC5) — proves what
   *  copy the user saw at decision time. Stored in the audit metadata
   *  alongside `acceptedAt` for FR12 immutability evidence. */
  contentHash: string;
  /** ISO 8601 UTC timestamp from the moment the user clicked Accept,
   *  as captured by the ConsentDialog itself (client clock, no
   *  server-trust). The backend stamps its own `requested_at`
   *  authoritatively. */
  acceptedAt: string;
}

export async function requestAccountDeletion(
  payload: AccountDeletionRequestPayload,
): Promise<AccountDeletionRequest> {
  return apiFetch<AccountDeletionRequest>("/api/v1/auth/me/account-deletion/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body: {
      password: payload.password,
      content_hash: payload.contentHash,
      accepted_at: payload.acceptedAt,
    },
  });
}

export async function getMyAccountDeletionStatus(): Promise<AccountDeletionRequest> {
  // Returns 404 if no in-flight request exists — caller catches `ApiError.status === 404`
  // and treats it as "no pending deletion".
  return apiFetch<AccountDeletionRequest>(
    "/api/v1/auth/me/account-deletion/status/",
    { method: "GET" },
  );
}

export async function getPublicAccountDeletionStatus(
  token: string,
): Promise<AccountDeletionPublicStatus> {
  return apiFetch<AccountDeletionPublicStatus>(
    `/api/v1/auth/account-deletion/${encodeURIComponent(token)}/`,
    { method: "GET" },
  );
}

export async function cancelAccountDeletion(
  token: string,
  password: string,
): Promise<{ detail: string }> {
  // Story 1.12 code review §P22: the public cancel endpoint is reached from a
  // logged-out session, so no CSRF cookie is normally present. DRF's
  // `SessionAuthentication` only enforces CSRF when an authenticated session
  // is in flight — anonymous POSTs bypass it. The asymmetry with
  // `requestAccountDeletion` (which sends `csrfToken`) is intentional and
  // mirrors the parental-consent decide endpoint shape from Story 1.4.
  return apiFetch<{ detail: string }>(
    `/api/v1/auth/account-deletion/${encodeURIComponent(token)}/cancel/`,
    {
      method: "POST",
      body: { password },
    },
  );
}
