/**
 * Typed client for the onboarding step-1 endpoints (Story 2.1 AC5).
 *
 * `GET /api/v1/students/me/onboarding/passions` — current profile shape or
 * empty defaults if the row doesn't exist yet.
 *
 * `PATCH /api/v1/students/me/onboarding/passions` — one sub-step at a time,
 * discriminated by `step`. Mixed-step payloads are rejected by the backend
 * serializer; the client mirrors the discriminated-union shape so that
 * mismatch trips TypeScript at compile time.
 */

import { apiFetch } from "@/lib/api/client";

const ENDPOINT = "/api/v1/students/me/onboarding/passions";

export type OnboardingStep1Status =
  | "pending"
  | "in_progress"
  | "completed"
  | "skipped"
  | "partial_skipped";

export type OnboardingInterets = {
  "1": string | null;
  "2": string | null;
  "3": string | null;
};

export type OnboardingStep1Snapshot = {
  passions: readonly string[];
  valeurs: readonly string[];
  interets: OnboardingInterets;
  onboarding_step1_status: OnboardingStep1Status;
  onboarding_step1_completed_at: string | null;
};

export type OnboardingStep1Patch =
  | { step: "passions"; passions: readonly string[] }
  | { step: "valeurs"; valeurs: readonly string[] }
  | { step: "interets"; interets: OnboardingInterets }
  | { step: "skip" };

/**
 * Factory returning a fresh empty snapshot each call.
 *
 * Pass 1 review M10 — the previous shared `EMPTY_ONBOARDING_SNAPSHOT`
 * constant was a foot-gun: every consumer received the same `interets`
 * sub-object reference, so any caller mutating it (or any TanStack
 * structural-sharing edge case) would taint the singleton across hook
 * instances. The factory pattern guarantees each consumer owns its
 * defaults. The `EMPTY_ONBOARDING_SNAPSHOT` named export is preserved
 * as a frozen alias for callers that only read it.
 */
export function makeEmptyOnboardingSnapshot(): OnboardingStep1Snapshot {
  return {
    passions: [],
    valeurs: [],
    interets: { "1": null, "2": null, "3": null },
    onboarding_step1_status: "pending",
    onboarding_step1_completed_at: null,
  };
}

export const EMPTY_ONBOARDING_SNAPSHOT: OnboardingStep1Snapshot = Object.freeze({
  ...makeEmptyOnboardingSnapshot(),
  interets: Object.freeze({ "1": null, "2": null, "3": null }) as OnboardingInterets,
}) as OnboardingStep1Snapshot;

export function fetchOnboardingSnapshot(signal?: AbortSignal): Promise<OnboardingStep1Snapshot> {
  return apiFetch<OnboardingStep1Snapshot>(ENDPOINT, { signal });
}

export function patchOnboardingStep1(
  payload: OnboardingStep1Patch,
  csrfToken: string,
): Promise<OnboardingStep1Snapshot> {
  return apiFetch<OnboardingStep1Snapshot>(ENDPOINT, {
    method: "PATCH",
    body: payload,
    csrfToken,
  });
}

// ---------------------------------------------------------------------------
// Step-2 — Niveau scolaire (Story 2.2)
// ---------------------------------------------------------------------------

const LEVEL_ENDPOINT = "/api/v1/students/me/onboarding/level";

export type OnboardingStep2Status = "pending" | "in_progress" | "completed" | "skipped";

export type OnboardingStep2Snapshot = {
  level: string | null;
  filiere: string | null;
  sous_filiere_techno: string | null;
  specialites: readonly string[];
  intended_track: string | null;
  postbac_year: string | null;
  postbac_formation_type: string | null;
  onboarding_step2_status: OnboardingStep2Status;
  onboarding_step2_completed_at: string | null;
  level_ref_version: string | null;
};

export type OnboardingStep2Patch = {
  commit?: boolean;
  skip?: boolean;
  level?: string | null;
  filiere?: string | null;
  sous_filiere_techno?: string | null;
  specialites?: readonly string[];
  intended_track?: string | null;
  postbac_year?: string | null;
  postbac_formation_type?: string | null;
  level_ref_version?: string;
};

export function makeEmptyStep2Snapshot(): OnboardingStep2Snapshot {
  return {
    level: null,
    filiere: null,
    sous_filiere_techno: null,
    specialites: [],
    intended_track: null,
    postbac_year: null,
    postbac_formation_type: null,
    onboarding_step2_status: "pending",
    onboarding_step2_completed_at: null,
    level_ref_version: null,
  };
}

export function fetchOnboardingStep2Snapshot(
  signal?: AbortSignal,
): Promise<OnboardingStep2Snapshot> {
  return apiFetch<OnboardingStep2Snapshot>(LEVEL_ENDPOINT, { signal });
}

export function patchOnboardingStep2(
  payload: OnboardingStep2Patch,
  csrfToken: string,
): Promise<OnboardingStep2Snapshot> {
  return apiFetch<OnboardingStep2Snapshot>(LEVEL_ENDPOINT, {
    method: "PATCH",
    body: payload,
    csrfToken,
  });
}
