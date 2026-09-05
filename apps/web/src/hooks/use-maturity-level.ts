"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";
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
  // Code-review fix (2026-09): same class of bug as `use-student-profile.ts`
  // — a bare `fetch("/api/v1/...")` with a relative path resolves against
  // the Next.js dev server, not the Django API, and 404s every time. Every
  // caller of this hook (`ProgressionModule` on `/accueil`, and `/profile`'s
  // maturity indicator) silently got `data: undefined` forever — on
  // `/accueil` that just meant an invisible module (guarded by `if
  // (!data) return null`); on `/profile` it crashed the whole page (see
  // `profile-page.tsx` fix in the same commit).
  return apiFetch<MaturityResponse>("/api/v1/students/me/profile/maturity");
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
