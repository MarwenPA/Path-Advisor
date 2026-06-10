"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchCsrfToken } from "@/lib/api/auth";
import { ApiError, readCsrfCookie } from "@/lib/api/client";
import {
  fetchOnboardingSnapshot,
  makeEmptyOnboardingSnapshot,
  patchOnboardingStep1,
  type OnboardingStep1Patch,
  type OnboardingStep1Snapshot,
} from "@/lib/api/onboarding";

const QUERY_KEY = ["onboarding", "step1"] as const;
// Pass 1 review M9 — namespace the draft by user ID so a shared device
// can't leak User A's selections into User B's onboarding. The legacy
// shared key `onboarding_step1_draft` is migrated on first read (any leftover
// global draft is dropped — it belonged to a previous user).
const DRAFT_STORAGE_PREFIX = "onboarding_step1_draft";
const LEGACY_DRAFT_STORAGE_KEY = "onboarding_step1_draft";

function draftKeyFor(userId: string | null | undefined): string {
  return userId ? `${DRAFT_STORAGE_PREFIX}:${userId}` : DRAFT_STORAGE_PREFIX;
}

type DraftSnapshot = Pick<OnboardingStep1Snapshot, "passions" | "valeurs" | "interets">;

function readDraft(key: string): DraftSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as DraftSnapshot;
  } catch {
    return null;
  }
}

function writeDraft(key: string, draft: DraftSnapshot): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(draft));
  } catch {
    // Quota / private mode — silently fall through, the PATCH still
    // wins when it eventually succeeds.
  }
}

function clearDraft(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
    // Pass 1 M9 — also nuke the legacy global key on every clear so any
    // pre-namespace draft left behind by an older version doesn't
    // resurface for a different user. Cheap, idempotent.
    if (key !== LEGACY_DRAFT_STORAGE_KEY) {
      window.localStorage.removeItem(LEGACY_DRAFT_STORAGE_KEY);
    }
  } catch {
    /* noop */
  }
}

async function getCsrf(): Promise<string> {
  return readCsrfCookie() ?? (await fetchCsrfToken());
}

/**
 * Drives the onboarding step-1 screen (Story 2.1 §AC5, §AC6).
 *
 * - `useQuery` fetches the server snapshot once on mount. The query data
 *   is hydrated from a `localStorage` draft when the network request is
 *   in flight — this keeps the screen warm under flaky connections and
 *   covers the AC6 "reprise after fermeture" path: a draft saved by a
 *   previous session re-applies before any HTTP roundtrip completes.
 * - `useMutation` performs the per-sub-step PATCH. On success the
 *   server snapshot replaces both the React Query cache and the local
 *   draft. On failure (network / 5xx), the local draft is preserved
 *   and `lastError` surfaces a typed reason for the caller to render
 *   the AC5 toast — "Pas de réseau ? Pas grave, on enregistre quand
 *   tu reviens." The caller (orchestrator) advances the sub-step
 *   regardless of PATCH outcome (UX > strict sync).
 *
 * Returns a stable object so callers can destructure inside effect
 * dep arrays without re-running on every render.
 */
/**
 * `userId` is the authenticated student's user ID (e.g. from
 * `fetchCurrentUser().id`). Pass 1 review M9 — the draft is now
 * keyed per-user so a shared device can't leak User A's selections
 * into User B's onboarding. When `userId` is `undefined` (server-side
 * render, anonymous) the hook falls back to the legacy global key
 * which the test suite has historically expected.
 */
export function useOnboardingStep1(userId?: string | null) {
  const queryClient = useQueryClient();
  const draftKey = React.useMemo(() => draftKeyFor(userId), [userId]);

  const query = useQuery<OnboardingStep1Snapshot>({
    queryKey: QUERY_KEY,
    queryFn: ({ signal }) => fetchOnboardingSnapshot(signal),
    // The draft is the initial data so the first render is hydrated even
    // before the network round-trip completes (AC6 — silent reprise).
    initialData: () => {
      const draft = readDraft(draftKey);
      if (!draft) return undefined;
      // Pass 1 M10 — use the factory (not the frozen const) so the
      // returned object is mutable and per-consumer.
      return { ...makeEmptyOnboardingSnapshot(), ...draft };
    },
    // `initialDataUpdatedAt: 0` marks the draft as already stale so TanStack
    // will fire the queryFn on mount and overwrite the optimistic draft
    // with the server's authoritative snapshot. Without this, the global
    // 30 s staleTime would keep the draft in place and never refetch.
    initialDataUpdatedAt: 0,
    // 30 s stale window AFTER the first network commit — keeps a sub-step
    // PATCH from triggering an immediate refetch of the very response we
    // just returned.
    staleTime: 30_000,
  });

  const mutation = useMutation<OnboardingStep1Snapshot, Error, OnboardingStep1Patch>({
    mutationFn: async (payload) => {
      const csrf = await getCsrf();
      return patchOnboardingStep1(payload, csrf);
    },
    onSuccess: (snapshot) => {
      queryClient.setQueryData(QUERY_KEY, snapshot);
      // Flush the draft once the server has confirmed the write — the
      // server snapshot is the new source of truth.
      clearDraft(draftKey);
    },
    // No automatic retry: the orchestrator decides whether to keep
    // local-only or surface the error. Retrying silently would cost
    // analytics fidelity and possibly double-emit step events.
    retry: false,
  });

  // Persist the current snapshot into the localStorage draft on every
  // change. Cheap (small payload) and runs once per state transition.
  // Pass 1 M10 — fall back to the factory so callers don't share a
  // mutable singleton. The empty fallback is computed unconditionally
  // (a conditional `useMemo` would violate the hooks-order rule).
  const emptyFallback = React.useMemo(() => makeEmptyOnboardingSnapshot(), []);
  const snapshot = query.data ?? emptyFallback;
  React.useEffect(() => {
    if (snapshot.onboarding_step1_status === "completed") {
      // Once the server confirms completion the draft no longer carries
      // useful state — keep localStorage clean so a later return to
      // /onboarding/step-1 (which AC10 redirects away) doesn't repopulate
      // an opacity-0 form.
      clearDraft(draftKey);
      return;
    }
    writeDraft(draftKey, {
      passions: snapshot.passions,
      valeurs: snapshot.valeurs,
      interets: snapshot.interets,
    });
  }, [snapshot, draftKey]);

  // Pass 1 review M6 — surface a typed `submitErrorKind` so the
  // orchestrator can distinguish a 4xx (permanent — block substep
  // advance) from a 5xx / network blip (transient — UX > strict sync).
  // The previous version treated every error the same, so a CSRF
  // misconfiguration looked like a network outage and the user kept
  // moving through sub-steps while nothing was saved server-side. A
  // localStorage wipe would then erase the entire onboarding silently.
  const submitErrorKind: "none" | "client" | "network" = React.useMemo(() => {
    const err = mutation.error;
    if (!err) return "none";
    if (err instanceof ApiError && err.status >= 400 && err.status < 500) return "client";
    return "network";
  }, [mutation.error]);

  return {
    snapshot,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
    submit: mutation.mutateAsync,
    isSubmitting: mutation.isPending,
    submitError: mutation.error,
    submitErrorKind,
    reset: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  } as const;
}

export const __TEST_ONLY__ = {
  DRAFT_STORAGE_KEY: LEGACY_DRAFT_STORAGE_KEY,
  DRAFT_STORAGE_PREFIX,
  draftKeyFor,
  QUERY_KEY,
};
