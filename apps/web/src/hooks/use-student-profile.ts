import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type BulletinsStatus = "pending" | "postponed" | "partial" | "completed";

export interface StudentProfile {
  id?: string;
  passions?: string[];
  valeurs?: string[];
  interets?: Record<string, string | null>;
  onboarding_step1_status?: string;
  bulletins_status: BulletinsStatus;
  bulletins_postponed_at: string | null;
  bulletins_postponed_banner_dismissed_until: string | null;
  level?: string | null;
  filiere?: string | null;
  specialites?: string[];
  sous_filiere_techno?: string | null;
  updated_at?: string;
}

const PROFILE_QUERY_KEY = ["student-profile"] as const;

async function fetchStudentProfile(): Promise<StudentProfile> {
  // Code-review fix (2026-09): this used to be a bare `fetch("/api/v1/...")`
  // — a relative path from a Client Component resolves against the Next.js
  // dev server (localhost:3000), which has no such route, not the Django
  // API (localhost:8000). Every request 404'd against Next itself and
  // `/profile` was stuck on "Chargement…" forever (the page only checks
  // `isLoading || !profile`, never the query's error state). `apiFetch`
  // is the one place in the codebase that knows the real API base URL
  // (`NEXT_PUBLIC_API_URL`) and forwards credentials — same rule every
  // other API module in `lib/api/*` already follows (see client.ts docstring).
  return apiFetch<StudentProfile>("/api/v1/students/me/profile");
}

export function useStudentProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchStudentProfile,
  });
}

async function postPostpone(): Promise<
  Pick<StudentProfile, "bulletins_status" | "bulletins_postponed_at">
> {
  return apiFetch("/api/v1/students/me/bulletins/postpone", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export function usePostponeBulletins() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postPostpone,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
    },
  });
}

async function postBannerDismiss(): Promise<
  Pick<StudentProfile, "bulletins_postponed_banner_dismissed_until">
> {
  return apiFetch("/api/v1/students/me/bulletins/banner/dismiss", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export function useDismissBulletinsBanner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postBannerDismiss,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
    },
  });
}

export function isBannerVisible(profile: StudentProfile): boolean {
  if (profile.bulletins_status !== "postponed") return false;
  const dismissedUntil = profile.bulletins_postponed_banner_dismissed_until;
  if (!dismissedUntil) return true;
  return new Date(dismissedUntil) < new Date();
}
