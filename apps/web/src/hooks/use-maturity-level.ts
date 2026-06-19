"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/client";
import type { MaturityLevel } from "@/lib/profile/maturity";
import type { MaturityNextAction } from "@/components/features/profile/profile-maturity-indicator";

export interface MaturityResponse {
  level: MaturityLevel;
  next_actions: Array<{
    icon: MaturityNextAction["icon"];
    label: string;
    benefit: string;
  }>;
  computed_at: string;
}

async function fetchMaturity(): Promise<MaturityResponse> {
  const res = await fetch("/api/v1/students/me/profile/maturity", {
    credentials: "include",
  });
  if (!res.ok) {
    throw new ApiError(res.status, "Failed to fetch profile maturity");
  }
  return res.json() as Promise<MaturityResponse>;
}

const MATURITY_QUERY_KEY = ["profile", "maturity"] as const;

export function useMaturityLevel(userId?: string | null) {
  return useQuery({
    queryKey: userId ? [...MATURITY_QUERY_KEY, userId] : MATURITY_QUERY_KEY,
    queryFn: fetchMaturity,
    staleTime: 30_000,
    enabled: !!userId,
  });
}
