/**
 * Access-list API client — Story 1.9 §T6.2.
 *
 * Mirrors the Django DTO `AccessListEntry` exactly. Keep the field names
 * 1:1 with the backend serializer (snake_case in transit) and let the
 * components destructure rather than introducing a transformer layer.
 */
import { apiFetch } from "./client";

export type TierType = "parent" | "school" | "counselor";

export interface AccessListEntry {
  id: string;
  tier_type: TierType;
  display_name: string;
  granted_at: string; // ISO 8601
  visible_data: readonly string[];
  masked_data: readonly string[];
  revocable: boolean;
  /** Story 6.11 — "date dernière consultation". `null` when the source
   * doesn't track per-access timestamps (e.g. a parental consent granted
   * before the parent had a Path-Advisor account). */
  last_accessed_at: string | null;
}

export interface AccessListResponse {
  results: AccessListEntry[];
}

export async function fetchAccessList(): Promise<AccessListResponse> {
  return apiFetch<AccessListResponse>("/api/v1/profile/access-list/");
}

export interface RevokeResponse {
  revoked: boolean;
  id: string;
}

/**
 * Story 1.10 §AC1 — POST /api/v1/profile/access-list/<id>/revoke/.
 * `contentHash` is computed by the ConsentDialog from the displayed props
 * and stored server-side as forensic proof (NOT a gate). Throws ApiError
 * on 404 (already revoked / unknown entry) so the caller can branch.
 */
export async function revokeAccessListEntry(
  id: string,
  contentHash: string,
): Promise<RevokeResponse> {
  return apiFetch<RevokeResponse>(`/api/v1/profile/access-list/${encodeURIComponent(id)}/revoke/`, {
    method: "POST",
    body: { content_hash: contentHash },
  });
}

/** Story 6.11 — one row of a 90-day access-history log. */
export interface AccessHistoryEntry {
  consulted_at: string; // ISO 8601
  metadata: Record<string, unknown>;
}

export async function fetchAccessHistory(id: string): Promise<{ results: AccessHistoryEntry[] }> {
  return apiFetch<{ results: AccessHistoryEntry[] }>(
    `/api/v1/profile/access-list/${encodeURIComponent(id)}/history/`,
  );
}

/** CSV export URL (a plain link, not a fetch — same pattern as
 * `ECOLE_REPORTING_EXPORT_URL`/`COHORT_REPORTING_EXPORT_URL`). */
export function buildAccessHistoryExportUrl(id: string): string {
  return `/api/v1/profile/access-list/${encodeURIComponent(id)}/history.csv/`;
}
