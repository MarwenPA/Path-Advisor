import * as React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import type { OnboardingStep1Snapshot } from "@/lib/api/onboarding";

const fetchSnapshotMock = vi.fn();
const patchSnapshotMock = vi.fn();

vi.mock("@/lib/api/onboarding", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/onboarding")>(
    "@/lib/api/onboarding",
  );
  return {
    ...actual,
    fetchOnboardingSnapshot: (...args: unknown[]) => fetchSnapshotMock(...args),
    patchOnboardingStep1: (...args: unknown[]) => patchSnapshotMock(...args),
  };
});

vi.mock("@/lib/api/auth", () => ({
  fetchCsrfToken: vi.fn().mockResolvedValue("test-csrf"),
}));

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return { ...actual, readCsrfCookie: vi.fn().mockReturnValue("cookie-csrf") };
});

import { __TEST_ONLY__, useOnboardingStep1 } from "./use-onboarding-step-1";

const { DRAFT_STORAGE_KEY, draftKeyFor } = __TEST_ONLY__;

const FRESH_SNAPSHOT: OnboardingStep1Snapshot = {
  passions: ["musique", "tech-code", "sport-corps"],
  valeurs: [],
  interets: { "1": null, "2": null, "3": null },
  onboarding_step1_status: "in_progress",
  onboarding_step1_completed_at: null,
};

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  }
  return Wrapper;
}

// Pass 2 PR2-H4 + PR2-H7 — the hook now needs a userId to (a) namespace
// the query key and (b) decide whether to hydrate from a stored draft.
// Tests pass a stable userId; the legacy-key migration is exercised in
// a dedicated test below.
const TEST_USER_ID = "usr_test_123";

function Probe({ userId = TEST_USER_ID }: { userId?: string | null }) {
  const hook = useOnboardingStep1(userId);
  return (
    <div>
      <span data-testid="passions">{hook.snapshot.passions.join(",")}</span>
      <span data-testid="status">{hook.snapshot.onboarding_step1_status}</span>
      <button
        type="button"
        onClick={() =>
          hook.submit({
            step: "passions",
            passions: ["musique", "tech-code", "sport-corps"],
          })
        }
      >
        submit
      </button>
    </div>
  );
}

describe("useOnboardingStep1", () => {
  beforeEach(() => {
    fetchSnapshotMock.mockReset();
    patchSnapshotMock.mockReset();
    window.localStorage.removeItem(DRAFT_STORAGE_KEY);
    window.localStorage.removeItem(draftKeyFor(TEST_USER_ID));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("hydrates initialData from localStorage draft (AC6 — silent reprise)", async () => {
    window.localStorage.setItem(
      draftKeyFor(TEST_USER_ID),
      JSON.stringify({
        passions: ["musique", "tech-code"],
        valeurs: [],
        interets: { "1": null, "2": null, "3": null },
      }),
    );
    // The fetch mock never resolves — we only assert the draft hydrates the
    // initial render, which is the AC6 "silent reprise" contract: a returning
    // user sees their last state before any network round-trip completes.
    fetchSnapshotMock.mockReturnValue(new Promise(() => {}));
    render(<Probe />, { wrapper: makeWrapper() });
    expect(screen.getByTestId("passions")).toHaveTextContent("musique,tech-code");
  });

  it("persists the current snapshot to localStorage on every snapshot change", async () => {
    fetchSnapshotMock.mockResolvedValue(FRESH_SNAPSHOT);
    render(<Probe />, { wrapper: makeWrapper() });
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("in_progress"));
    const stored = JSON.parse(window.localStorage.getItem(draftKeyFor(TEST_USER_ID)) ?? "null");
    expect(stored).toMatchObject({ passions: ["musique", "tech-code", "sport-corps"] });
  });

  it("clears the localStorage draft when the snapshot reports `completed`", async () => {
    // Seed a non-empty draft + mock fetch to return completed in one go.
    // The component renders, the effect fires once the snapshot lands, and
    // the draft is removed from storage (AC10 prep — completing kills the
    // draft so a later /step-1 navigation can't rehydrate stale data).
    window.localStorage.setItem(
      draftKeyFor(TEST_USER_ID),
      JSON.stringify({
        passions: ["foo"],
        valeurs: [],
        interets: { "1": null, "2": null, "3": null },
      }),
    );
    fetchSnapshotMock.mockResolvedValue({
      ...FRESH_SNAPSHOT,
      onboarding_step1_status: "completed" as const,
      onboarding_step1_completed_at: "2026-06-11T00:00:00Z",
    });
    render(<Probe />, { wrapper: makeWrapper() });
    // Allow TanStack to commit the resolved snapshot.
    await waitFor(() => expect(fetchSnapshotMock).toHaveBeenCalled());
    // The Probe shows the initial state from the draft (TanStack initialData
    // wins until refetch); the effect that clears localStorage on completion
    // is what we actually assert.
    await waitFor(() =>
      expect(window.localStorage.getItem(draftKeyFor(TEST_USER_ID))).toBeNull(),
    );
  });

  // Pass 2 PR2-H7 — a stale LEGACY-keyed draft (left behind by a previous
  // user or an older app version) must NOT leak into the namespaced read
  // path AND must be eagerly nuked the moment we know the current userId.
  it("eagerly removes the legacy global draft key on mount when userId is known (PR2-H7)", async () => {
    window.localStorage.setItem(
      DRAFT_STORAGE_KEY,
      JSON.stringify({
        passions: ["leaked-from-prior-user"],
        valeurs: [],
        interets: { "1": null, "2": null, "3": null },
      }),
    );
    fetchSnapshotMock.mockReturnValue(new Promise(() => {}));
    render(<Probe userId={TEST_USER_ID} />, { wrapper: makeWrapper() });
    // The cleanup effect runs after mount; the legacy key disappears even
    // though no PATCH has succeeded yet.
    await waitFor(() =>
      expect(window.localStorage.getItem(DRAFT_STORAGE_KEY)).toBeNull(),
    );
    // The namespaced key was never written (no draft existed for this user)
    // so the snapshot stays empty — User A's "leaked-from-prior-user" is
    // not visible.
    expect(screen.getByTestId("passions").textContent).toBe("");
  });

  // Pass 2 PR2-H4 — TanStack cache must be per-user. A logout/login flow
  // on the same tab now produces a fresh cache entry for the new userId
  // instead of serving the prior user's snapshot.
  it("namespaces the query key by userId so a userId change refetches", async () => {
    const snapshotA = { ...FRESH_SNAPSHOT, passions: ["a", "b", "c"] };
    const snapshotB = { ...FRESH_SNAPSHOT, passions: ["x", "y", "z"] };
    fetchSnapshotMock.mockImplementation(() => Promise.resolve(snapshotA));
    const { rerender } = render(<Probe userId="usr_A" />, { wrapper: makeWrapper() });
    await waitFor(() => expect(screen.getByTestId("passions")).toHaveTextContent("a,b,c"));
    fetchSnapshotMock.mockImplementation(() => Promise.resolve(snapshotB));
    rerender(<Probe userId="usr_B" />);
    await waitFor(() => expect(screen.getByTestId("passions")).toHaveTextContent("x,y,z"));
  });
});
