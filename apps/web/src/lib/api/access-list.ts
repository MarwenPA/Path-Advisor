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
