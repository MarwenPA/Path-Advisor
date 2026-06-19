/**
 * Vitest golden-snapshot tests for computeMaturity() — Story 2.7 AC2 + AC9.
 * Mirrors the 15 Python cases in test_profile_maturity.py.
 * Also validates alignment against the shared JSON golden file.
 */

import { describe, expect, it } from "vitest";
import goldenCases from "../golden-maturity.test.json";
import { computeMaturity, type MaturityLevel, type ProfileSnapshot } from "../maturity";

// ---------------------------------------------------------------------------
// Inline 15 golden cases (mirrors Python test_profile_maturity.py)
// ---------------------------------------------------------------------------

const GOLDEN: Array<[string, ProfileSnapshot, MaturityLevel]> = [
  [
    "brand-new user (both steps pending, bulletins pending)",
    { onboarding_step1_status: "pending", passions_count: 0, onboarding_step2_status: "pending", bulletins_status: "pending" },
    "base",
  ],
  [
    "step1 skipped + step2 skipped + bulletins pending",
    { onboarding_step1_status: "skipped", passions_count: 0, onboarding_step2_status: "skipped", bulletins_status: "pending" },
    "base",
  ],
  [
    "step1 completed + step2 skipped + bulletins postponed",
    { onboarding_step1_status: "completed", passions_count: 5, onboarding_step2_status: "skipped", bulletins_status: "postponed" },
    "base",
  ],
  [
    "step1 partial_skipped (≥3 passions) + step2 completed + bulletins pending",
    { onboarding_step1_status: "partial_skipped", passions_count: 3, onboarding_step2_status: "completed", bulletins_status: "pending" },
    "base",
  ],
  [
    "step1 in_progress (no passions) + step2 pending + bulletins pending",
    { onboarding_step1_status: "in_progress", passions_count: 0, onboarding_step2_status: "pending", bulletins_status: "pending" },
    "base",
  ],
  [
    "step1 completed + step2 completed + bulletins postponed",
    { onboarding_step1_status: "completed", passions_count: 6, onboarding_step2_status: "completed", bulletins_status: "postponed" },
    "base",
  ],
  [
    "step1 completed + step2 completed + bulletins partial → enriched",
    { onboarding_step1_status: "completed", passions_count: 5, onboarding_step2_status: "completed", bulletins_status: "partial" },
    "enriched",
  ],
  [
    "step1 skipped + step2 skipped + bulletins partial → enriched",
    { onboarding_step1_status: "skipped", passions_count: 0, onboarding_step2_status: "skipped", bulletins_status: "partial" },
    "enriched",
  ],
  [
    "partial_skipped (≥3 passions) + step2 skipped + bulletins partial → enriched",
    { onboarding_step1_status: "partial_skipped", passions_count: 4, onboarding_step2_status: "skipped", bulletins_status: "partial" },
    "enriched",
  ],
  [
    "in_progress (2 passions <3) + step2 pending + bulletins partial → enriched",
    { onboarding_step1_status: "in_progress", passions_count: 2, onboarding_step2_status: "pending", bulletins_status: "partial" },
    "enriched",
  ],
  [
    "step1 completed + step2 completed + bulletins completed → complete",
    { onboarding_step1_status: "completed", passions_count: 5, onboarding_step2_status: "completed", bulletins_status: "completed" },
    "complete",
  ],
  [
    "step1 completed (8 passions) + step2 completed + bulletins completed → complete",
    { onboarding_step1_status: "completed", passions_count: 8, onboarding_step2_status: "completed", bulletins_status: "completed" },
    "complete",
  ],
  [
    "step1 skipped + step2 completed + bulletins completed → enriched (step1 not completed)",
    { onboarding_step1_status: "skipped", passions_count: 0, onboarding_step2_status: "completed", bulletins_status: "completed" },
    "enriched",
  ],
  [
    "step1 completed + step2 skipped + bulletins completed → enriched (step2 not completed)",
    { onboarding_step1_status: "completed", passions_count: 5, onboarding_step2_status: "skipped", bulletins_status: "completed" },
    "enriched",
  ],
  [
    "partial_skipped (1 passion <3) + step2 pending + bulletins completed → enriched",
    { onboarding_step1_status: "partial_skipped", passions_count: 1, onboarding_step2_status: "pending", bulletins_status: "completed" },
    "enriched",
  ],
];

describe("computeMaturity — 15 golden cases", () => {
  it.each(GOLDEN)("%s", (_label, snap, expected) => {
    expect(computeMaturity(snap)).toBe(expected);
  });
});

// ---------------------------------------------------------------------------
// JSON golden file alignment (anti-drift between Python and TS)
// ---------------------------------------------------------------------------

describe("computeMaturity — JSON golden alignment (anti-drift)", () => {
  it.each(goldenCases.map((c) => [c.id, c] as const))("case %s", (_id, c) => {
    const snap: ProfileSnapshot = {
      onboarding_step1_status: c.onboarding_step1_status,
      passions_count: c.passions_count,
      onboarding_step2_status: c.onboarding_step2_status,
      bulletins_status: c.bulletins_status,
    };
    expect(computeMaturity(snap)).toBe(c.expected);
  });
});
