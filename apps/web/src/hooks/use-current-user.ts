"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchCurrentUser, type CurrentUser } from "@/lib/api/auth";

export const CURRENT_USER_QUERY_KEY = ["current-user"] as const;

/**
 * Shared authenticated-user query — Story 10.6.
 *
 * Until now every consumer (`mfa-banner`, `ProgressionModule`,
 * `outreach-section`, …) ran its own one-shot `fetchCurrentUser()` in a
 * `useEffect`. This hook gives them a common cache key so N banners on one
 * page cost one request. `pollWhile` turns on a conditional refetch interval
 * (the `use-ocr-job` pattern): return the delay in ms while the condition
 * holds, and the polling stops by itself once it resolves.
 *
 * `retry: false` — a 401 means the session is gone; retrying only delays the
 * redirect the next server navigation will perform.
 */
export function useCurrentUser(options?: {
  pollWhile?: (user: CurrentUser | undefined) => number | false;
}) {
  const pollWhile = options?.pollWhile;
  return useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: fetchCurrentUser,
    staleTime: 30_000,
    retry: false,
    refetchInterval: pollWhile
      ? (query: { state: { data?: CurrentUser } }) => pollWhile(query.state.data)
      : undefined,
  });
}
