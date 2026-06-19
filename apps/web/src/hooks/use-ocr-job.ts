"use client";

import { useQueries, useQuery } from "@tanstack/react-query";

export type OCRJobStatus = "pending" | "running" | "succeeded" | "failed" | "timeout";

export type OCRStatusResponse = {
  bulletin_id: string;
  status: OCRJobStatus;
  extraction: {
    normalized_fields: Array<{
      key: string;
      value: string;
      confidence: number;
      unmapped?: boolean;
      canonical_id?: string | null;
      raw?: string;
    }>;
    confidence_avg: number;
    is_low_quality: boolean;
  } | null;
  error: string | null;
};

async function fetchOCRStatus(bulletinId: string): Promise<OCRStatusResponse> {
  const res = await fetch(
    `/api/v1/students/me/bulletins/ocr/status?bulletin_id=${bulletinId}`,
    { credentials: "include" }
  );
  if (!res.ok) throw new Error(`OCR status fetch failed: ${res.status}`);
  return res.json();
}

function isTerminal(status?: string) {
  return status === "succeeded" || status === "failed" || status === "timeout";
}

const queryOptions = (bulletinId: string) => ({
  queryKey: ["ocr-status", bulletinId] as const,
  queryFn: () => fetchOCRStatus(bulletinId),
  refetchInterval: (query: { state: { data?: OCRStatusResponse } }) => {
    const s = query.state.data?.status;
    return !s || s === "pending" || s === "running" ? 2000 : false;
  },
  retry: (failureCount: number) => failureCount < 5,
  retryDelay: (attempt: number) => Math.min(2000 * Math.pow(2, attempt), 30_000),
});

/** Single-bulletin poll. */
export function useOCRJob(bulletinId: string | null) {
  return useQuery({
    ...queryOptions(bulletinId ?? "__disabled__"),
    enabled: !!bulletinId,
  });
}

/** Multi-bulletin poll (#2) — resolves when ALL bulletins reach a terminal state. */
export function useOCRJobs(bulletinIds: string[]) {
  const queries = useQueries({
    queries: bulletinIds.map((id) => ({
      ...queryOptions(id),
      enabled: bulletinIds.length > 0,
    })),
  });

  const allDone =
    queries.length > 0 && queries.every((q) => isTerminal(q.data?.status));
  const allSucceeded =
    queries.length > 0 && queries.every((q) => q.data?.status === "succeeded");
  const anyFailed = queries.some(
    (q) => q.data?.status === "failed" || q.data?.status === "timeout"
  );
  const firstStatus = queries[0]?.data?.status;

  return { queries, allDone, allSucceeded, anyFailed, firstStatus };
}
