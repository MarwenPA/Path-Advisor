"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type ErrorType = "description_inexacte" | "debouches_perimes" | "lien_casse" | "autre";

export interface ReportPayload {
  error_type: ErrorType;
  location?: string | null;
  comment?: string | null;
}

interface ReportResponse {
  id: string;
  status: string;
}

async function submitReport(slug: string, payload: ReportPayload): Promise<ReportResponse> {
  const csrf = readCsrfCookie() ?? "";
  return apiFetch<ReportResponse>(`/api/v1/professions/${slug}/reports/`, {
    method: "POST",
    body: JSON.stringify(payload),
    headers: { "X-CSRFToken": csrf },
  });
}

export function useReportProfessionError(slug: string) {
  return useMutation({
    mutationFn: (payload: ReportPayload) => submitReport(slug, payload),
  });
}
