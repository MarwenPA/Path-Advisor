/**
 * Back-office fetchers — moderation queue des signalements (Story 9.3).
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type ReportStatus = "pending" | "resolved" | "dismissed" | "info_requested";

export interface AdminReport {
  id: string;
  profession: { slug: string; name: string };
  reporter_email: string | null;
  error_type: string;
  error_type_label?: string;
  location: string | null;
  comment: string | null;
  status: ReportStatus;
  created_at: string;
  overdue: boolean;
  admin_note: string;
}

export interface AdminReportList {
  count: number;
  next: string | null;
  previous: string | null;
  overdue_count: number;
  results: AdminReport[];
}

export async function fetchAdminReports(
  query: { status?: string; error_type?: string; page?: number } = {},
): Promise<AdminReportList> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) params.set(key, String(value));
  }
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  return apiFetch<AdminReportList>(`/api/v1/admin/professions/reports/${suffix}`);
}

export async function actOnReport(
  reportId: string,
  action: "resolve" | "dismiss" | "request-info",
  body: { note?: string; reason?: string; message?: string } = {},
): Promise<{ id: string; status: ReportStatus }> {
  return apiFetch<{ id: string; status: ReportStatus }>(
    `/api/v1/admin/professions/reports/${reportId}/${action}/`,
    { method: "POST", csrfToken: readCsrfCookie() ?? undefined, body },
  );
}
