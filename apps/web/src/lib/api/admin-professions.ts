/**
 * Back-office fetchers — professions referential (Story 9.1).
 *
 * Mirrors `apps/api/apps/professions/views.py` admin endpoints
 * (`IsPathAdmin`, MFA enforced server-side). Every mutation carries the
 * CSRF token like the rest of the authenticated app.
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type ProfessionStatus = "draft" | "published" | "archived";

export interface AdminProfession {
  id: string;
  slug: string;
  name: string;
  description: string;
  daily_routine: string;
  requirements_json: Array<{ type?: string; label: string }>;
  prospects_text: string;
  median_salary_eur: number | null;
  salary_range_json: { min?: number; max?: number; source?: string } | null;
  signals_json: {
    passions?: string[];
    valeurs?: string[];
    specialites?: string[];
    keywords?: string[];
  };
  level_compatibility: string[];
  sector: string;
  rome_code: string | null;
  sources_json: string[];
  is_active: boolean;
  status: ProfessionStatus;
  created_at: string;
  updated_at: string;
}

export interface AdminProfessionList {
  count: number;
  next: string | null;
  previous: string | null;
  results: AdminProfession[];
}

export interface ProfessionRevision {
  id: string;
  action: "created" | "updated" | "status_changed" | "rolled_back";
  snapshot: Record<string, unknown>;
  editor_email: string | null;
  restored_from_id: string | null;
  created_at: string;
}

export interface AdminProfessionQuery {
  q?: string;
  status?: ProfessionStatus | "";
  sort?: string;
  page?: number;
}

export async function fetchAdminProfessions(
  query: AdminProfessionQuery = {},
): Promise<AdminProfessionList> {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.status) params.set("status", query.status);
  if (query.sort) params.set("sort", query.sort);
  if (query.page) params.set("page", String(query.page));
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  return apiFetch<AdminProfessionList>(`/api/v1/admin/professions/${suffix}`);
}

export async function fetchAdminProfession(slug: string): Promise<AdminProfession> {
  return apiFetch<AdminProfession>(`/api/v1/admin/professions/${slug}/`);
}

export type AdminProfessionPayload = Omit<
  AdminProfession,
  "id" | "is_active" | "created_at" | "updated_at"
>;

export async function createAdminProfession(
  payload: AdminProfessionPayload,
): Promise<AdminProfession> {
  return apiFetch<AdminProfession>("/api/v1/admin/professions/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}

export async function updateAdminProfession(
  slug: string,
  payload: Partial<AdminProfessionPayload>,
): Promise<AdminProfession> {
  return apiFetch<AdminProfession>(`/api/v1/admin/professions/${slug}/`, {
    method: "PATCH",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}

export async function archiveAdminProfession(slug: string): Promise<AdminProfession> {
  return apiFetch<AdminProfession>(`/api/v1/admin/professions/${slug}/archive/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export async function fetchProfessionRevisions(
  slug: string,
): Promise<{ revisions: ProfessionRevision[] }> {
  return apiFetch<{ revisions: ProfessionRevision[] }>(
    `/api/v1/admin/professions/${slug}/revisions/`,
  );
}

export async function rollbackAdminProfession(
  slug: string,
  revisionId: string,
): Promise<AdminProfession> {
  return apiFetch<AdminProfession>(`/api/v1/admin/professions/${slug}/rollback/${revisionId}/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}
