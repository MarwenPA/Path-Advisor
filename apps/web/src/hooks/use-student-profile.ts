import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export type BulletinsStatus = "pending" | "postponed" | "partial" | "completed";

export interface StudentProfile {
  bulletins_status: BulletinsStatus;
  bulletins_postponed_at: string | null;
  bulletins_postponed_banner_dismissed_until: string | null;
}

const PROFILE_QUERY_KEY = ["student-profile"] as const;

async function fetchStudentProfile(): Promise<StudentProfile> {
  const res = await fetch("/api/v1/students/me/profile");
  if (!res.ok) throw new Error("Failed to fetch student profile");
  return res.json();
}

export function useStudentProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchStudentProfile,
  });
}

async function postPostpone(): Promise<Pick<StudentProfile, "bulletins_status" | "bulletins_postponed_at">> {
  const res = await fetch("/api/v1/students/me/bulletins/postpone", { method: "POST" });
  if (!res.ok) throw new Error("Failed to postpone bulletins");
  return res.json();
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

async function postBannerDismiss(): Promise<Pick<StudentProfile, "bulletins_postponed_banner_dismissed_until">> {
  const res = await fetch("/api/v1/students/me/bulletins/banner/dismiss", { method: "POST" });
  if (!res.ok) throw new Error("Failed to dismiss banner");
  return res.json();
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
