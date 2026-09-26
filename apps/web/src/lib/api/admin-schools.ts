/**
 * Back-office fetchers — schools referential + Parcoursup calendar
 * (Story 9.2). Mirrors `AdminSchoolViewSet` + the milestone admin views.
 */

import { API_BASE_URL, apiFetch, readCsrfCookie } from "@/lib/api/client";

export type SchoolStatus = "draft" | "published" | "archived";

export interface AdminSchool {
  id: string;
  slug: string;
  name: string;
  type: string;
  city: string;
  region: string;
  postal_code: string;
  selectivity_index: number;
  public_private: string;
  description: string;
  official_url: string;
  status: SchoolStatus;
  is_active: boolean;
  updated_at?: string;
  [key: string]: unknown;
}

export interface AdminSchoolList {
  count: number;
  next: string | null;
  previous: string | null;
  results: AdminSchool[];
}

export interface SchoolRevision {
  id: string;
  action: "created" | "updated" | "status_changed" | "rolled_back" | "imported";
  snapshot: Record<string, unknown>;
  editor_email: string | null;
  restored_from_id: string | null;
  created_at: string;
}

export interface CsvImportReport {
  created: string[];
  conflicts: Array<{
    line: number;
    slug: string;
    existing: { name: string; city: string; status: SchoolStatus };
    incoming: Record<string, string>;
  }>;
  errors: Array<{ line: number; errors: Record<string, string[]> }>;
}

export async function fetchAdminSchools(
  query: { q?: string; type?: string; region?: string; status?: string; page?: number } = {},
): Promise<AdminSchoolList> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) params.set(key, String(value));
  }
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  return apiFetch<AdminSchoolList>(`/api/v1/admin/schools/${suffix}`);
}

export async function fetchAdminSchool(slug: string): Promise<AdminSchool> {
  return apiFetch<AdminSchool>(`/api/v1/admin/schools/${slug}/`);
}

export async function createAdminSchool(payload: Record<string, unknown>): Promise<AdminSchool> {
  return apiFetch<AdminSchool>("/api/v1/admin/schools/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}

export async function updateAdminSchool(
  slug: string,
  payload: Record<string, unknown>,
): Promise<AdminSchool> {
  return apiFetch<AdminSchool>(`/api/v1/admin/schools/${slug}/`, {
    method: "PATCH",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}

export async function archiveAdminSchool(slug: string): Promise<AdminSchool> {
  return apiFetch<AdminSchool>(`/api/v1/admin/schools/${slug}/archive/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export async function fetchSchoolRevisions(slug: string): Promise<{ revisions: SchoolRevision[] }> {
  return apiFetch<{ revisions: SchoolRevision[] }>(`/api/v1/admin/schools/${slug}/revisions/`);
}

export async function rollbackAdminSchool(slug: string, revisionId: string): Promise<AdminSchool> {
  return apiFetch<AdminSchool>(`/api/v1/admin/schools/${slug}/rollback/${revisionId}/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export async function importSchoolsCsv(file: File): Promise<CsvImportReport> {
  const form = new FormData();
  form.append("file", file);
  const csrf = readCsrfCookie() ?? "";
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/schools/import-csv/`, {
    method: "POST",
    credentials: "include",
    headers: csrf ? { "X-CSRFToken": csrf } : undefined,
    body: form,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw Object.assign(new Error("import failed"), {
      status: response.status,
      detail: (detail as { detail?: string }).detail,
    });
  }
  return (await response.json()) as CsvImportReport;
}

// --- Jalons Parcoursup (amendement 8.3) -----------------------------------

export interface AdminMilestone {
  id: number;
  kind: string;
  kind_label: string;
  campaign: string;
  date: string;
  notify_days_before: number;
  notified_at: string | null;
}

export async function fetchAdminMilestones(): Promise<{ milestones: AdminMilestone[] }> {
  return apiFetch<{ milestones: AdminMilestone[] }>("/api/v1/admin/parcoursup-milestones/");
}

export async function createAdminMilestone(payload: {
  kind: string;
  campaign: string;
  date: string;
  notify_days_before: number;
}): Promise<{ id: number }> {
  return apiFetch<{ id: number }>("/api/v1/admin/parcoursup-milestones/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}

export async function updateAdminMilestone(
  id: number,
  payload: Partial<{ date: string; notify_days_before: number }>,
): Promise<{ id: number }> {
  return apiFetch<{ id: number }>(`/api/v1/admin/parcoursup-milestones/${id}/`, {
    method: "PATCH",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}
