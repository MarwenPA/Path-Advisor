/**
 * API client for the school-side reception of early-outreach requests —
 * Story 5.6. `school_admin`-only endpoints (RBAC enforced server-side —
 * this client has no knowledge of the boundary, it just calls the URLs).
 */
import { apiFetch } from "@/lib/api/client";

export type EcoleOutreachStatus = "pending" | "responded" | "expired_7d";

export interface EcoleOutreachListItem {
  id: string;
  student_age: number | null;
  profession_name: string;
  parcours_label: string | null;
  status: EcoleOutreachStatus;
  created_at: string;
}

export interface EcoleOutreachDetail extends EcoleOutreachListItem {
  motivation_text: string;
}

export interface PaginatedEcoleOutreach {
  count: number;
  next: string | null;
  previous: string | null;
  results: EcoleOutreachListItem[];
}

export interface EcoleOutreachQueueParams {
  status?: EcoleOutreachStatus;
  ordering?: "created_at" | "-created_at";
}

export async function fetchEcoleOutreachQueue(
  params: EcoleOutreachQueueParams = {},
): Promise<PaginatedEcoleOutreach> {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.ordering) search.set("ordering", params.ordering);
  const qs = search.toString();
  return apiFetch<PaginatedEcoleOutreach>(`/api/v1/ecole/outreach/${qs ? `?${qs}` : ""}`);
}

export async function fetchEcoleOutreachDetail(outreachId: string): Promise<EcoleOutreachDetail> {
  return apiFetch<EcoleOutreachDetail>(`/api/v1/ecole/outreach/${encodeURIComponent(outreachId)}/`);
}
