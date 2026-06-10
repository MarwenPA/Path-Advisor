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

export const EMPTY_ONBOARDING_SNAPSHOT: OnboardingStep1Snapshot = {
  passions: [],
  valeurs: [],
  interets: { "1": null, "2": null, "3": null },
  onboarding_step1_status: "pending",
  onboarding_step1_completed_at: null,
};

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
