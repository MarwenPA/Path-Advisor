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
  return apiFetch<RevokeResponse>(
    `/api/v1/profile/access-list/${encodeURIComponent(id)}/revoke/`,
    {
      method: "POST",
      body: { content_hash: contentHash },
    },
  );
}
