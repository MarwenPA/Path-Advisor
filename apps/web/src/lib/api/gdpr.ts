/**
 * Typed wrappers around `/api/v1/me/gdpr-exports*` (Story 1.11).
 *
 * Every call goes through `apiFetch` so RFC 7807 errors surface as typed
 * `ApiError` and the CSRF cookie pre-flight stays consistent with the rest
 * of the app (Story 1.3 pattern).
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type GdprExportStatus = "pending" | "in_progress" | "ready" | "expired" | "failed";

export interface GdprExportRequest {
  id: string;
  status: GdprExportStatus;
  requested_at: string;
  ready_at: string | null;
  expires_at: string | null;
  download_count: number;
  error_code: string | null;
  error_message: string | null;
}

export interface GdprExportList {
  next: string | null;
  previous: string | null;
  results: GdprExportRequest[];
}

export async function listGdprExports(): Promise<GdprExportList> {
  return apiFetch<GdprExportList>("/api/v1/me/gdpr-exports/", { method: "GET" });
}

export async function getGdprExport(id: string): Promise<GdprExportRequest> {
  return apiFetch<GdprExportRequest>(`/api/v1/me/gdpr-exports/${id}/`, {
    method: "GET",
  });
}

export async function createGdprExport(): Promise<GdprExportRequest> {
  return apiFetch<GdprExportRequest>("/api/v1/me/gdpr-exports/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

/**
 * Returns the absolute URL the browser must navigate to in order to trigger
 * the download. The actual S3 redirect happens server-side; we never expose
 * the presigned URL in client JS.
 */
export function buildGdprDownloadUrl(id: string): string {
  // Same-origin path — the API base URL is wired via the next.config rewrite
  // (Story 1.5 will own the cross-origin variant).
  return `/api/v1/me/gdpr-exports/${id}/download/`;
}
