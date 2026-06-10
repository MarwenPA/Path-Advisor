"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchCsrfToken } from "@/lib/api/auth";
import { readCsrfCookie } from "@/lib/api/client";
import {
  EMPTY_ONBOARDING_SNAPSHOT,
  fetchOnboardingSnapshot,
  patchOnboardingStep1,
  type OnboardingStep1Patch,
  type OnboardingStep1Snapshot,
} from "@/lib/api/onboarding";

const QUERY_KEY = ["onboarding", "step1"] as const;
const DRAFT_STORAGE_KEY = "onboarding_step1_draft";

type DraftSnapshot = Pick<OnboardingStep1Snapshot, "passions" | "valeurs" | "interets">;

function readDraft(): DraftSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(DRAFT_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as DraftSnapshot;
  } catch {
    return null;
  }
}

function writeDraft(draft: DraftSnapshot): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // Quota / private mode — silently fall through, the PATCH still
    // wins when it eventually succeeds.
  }
}

function clearDraft(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(DRAFT_STORAGE_KEY);
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
export function useOnboardingStep1() {
  const queryClient = useQueryClient();

  const query = useQuery<OnboardingStep1Snapshot>({
    queryKey: QUERY_KEY,
    queryFn: ({ signal }) => fetchOnboardingSnapshot(signal),
    // The draft is the initial data so the first render is hydrated even
    // before the network round-trip completes (AC6 — silent reprise).
    initialData: () => {
      const draft = readDraft();
      if (!draft) return undefined;
      return { ...EMPTY_ONBOARDING_SNAPSHOT, ...draft };
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
      clearDraft();
    },
    // No automatic retry: the orchestrator decides whether to keep
    // local-only or surface the error. Retrying silently would cost
    // analytics fidelity and possibly double-emit step events.
    retry: false,
  });

  // Persist the current snapshot into the localStorage draft on every
  // change. Cheap (small payload) and runs once per state transition.
  const snapshot = query.data ?? EMPTY_ONBOARDING_SNAPSHOT;
  React.useEffect(() => {
    if (snapshot.onboarding_step1_status === "completed") {
      // Once the server confirms completion the draft no longer carries
      // useful state — keep localStorage clean so a later return to
      // /onboarding/step-1 (which AC10 redirects away) doesn't repopulate
      // an opacity-0 form.
      clearDraft();
      return;
    }
    writeDraft({
      passions: snapshot.passions,
      valeurs: snapshot.valeurs,
      interets: snapshot.interets,
    });
  }, [snapshot]);

  return {
    snapshot,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
    submit: mutation.mutateAsync,
    isSubmitting: mutation.isPending,
    submitError: mutation.error,
    reset: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  } as const;
}

export const __TEST_ONLY__ = {
  DRAFT_STORAGE_KEY,
  QUERY_KEY,
};
