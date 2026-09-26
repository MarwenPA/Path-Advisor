/**
 * Back-office fetchers — modération (Story 9.4) : motivations élèves +
 * commentaires libres des écoles (amendement revue Epic 8, P2-5).
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface Prescreen {
  pii: string[];
  risk: string[];
}

export interface PendingMotivation {
  id: string;
  student_email: string;
  school: { slug: string; name: string };
  profession_name: string;
  motivation_text: string;
  created_at: string;
  business_hours_age: number;
  overdue: boolean;
  prescreen: Prescreen;
}

export interface PendingSchoolComment {
  id: string;
  school: { slug: string; name: string };
  action: string;
  comment: string;
  created_at: string;
  business_hours_age: number;
  overdue: boolean;
  prescreen: Prescreen;
}

export async function fetchPendingMotivations(): Promise<{
  results: PendingMotivation[];
  overdue_count: number;
}> {
  return apiFetch("/api/v1/admin/moderation/motivations/");
}

export async function actOnMotivation(
  id: string,
  action: "approve" | "reject",
  body: { category?: string; reason?: string } = {},
): Promise<{ id: string; status: string }> {
  return apiFetch(`/api/v1/admin/moderation/motivations/${id}/${action}/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body,
  });
}

export async function fetchPendingSchoolComments(): Promise<{
  results: PendingSchoolComment[];
  overdue_count: number;
}> {
  return apiFetch("/api/v1/admin/moderation/school-comments/");
}

export async function actOnSchoolComment(
  id: string,
  action: "approve" | "reject",
): Promise<{ id: string; comment_status: string }> {
  return apiFetch(`/api/v1/admin/moderation/school-comments/${id}/${action}/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}
