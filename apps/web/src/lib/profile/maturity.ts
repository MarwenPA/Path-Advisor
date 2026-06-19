/**
 * Profile maturity computation — Story 2.7 AC2.
 * Pure TypeScript function — no React, no fetch, no side effects.
 * Shared logic with Python: apps/api/apps/students/profile_maturity.py
 * Both implementations are validated against the same golden JSON.
 *
 * Principle: 3 qualitative states only — NEVER a percentage.
 */

export type MaturityLevel = "base" | "enriched" | "complete";

export interface ProfileSnapshot {
  onboarding_step1_status: string;
  passions_count: number;
  onboarding_step2_status: string;
  bulletins_status: string;
}

const BULLETINS_ENRICHED = new Set(["partial"]);
const BULLETINS_COMPLETE = new Set(["completed"]);

function satisfiesComplete(snap: ProfileSnapshot): boolean {
  return (
    snap.onboarding_step1_status === "completed" &&
    snap.onboarding_step2_status === "completed" &&
    BULLETINS_COMPLETE.has(snap.bulletins_status)
  );
}

export function computeMaturity(snap: ProfileSnapshot): MaturityLevel {
  if (satisfiesComplete(snap)) return "complete";
  if (
    BULLETINS_ENRICHED.has(snap.bulletins_status) ||
    BULLETINS_COMPLETE.has(snap.bulletins_status)
  ) {
    return "enriched";
  }
  return "base";
}
