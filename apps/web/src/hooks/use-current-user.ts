"use client";

import { useEffect, useRef, useState } from "react";

import { fetchCurrentUser, type CurrentUser } from "@/lib/api/auth";

/**
 * Shared authenticated-user read with optional polling — Story 10.6.
 *
 * Plain fetch + chained `setTimeout` (the `AdmissionStatPoller` pattern,
 * ADD-8: no WebSocket in MVP), NOT TanStack Query — deliberately. A first
 * version used `useQuery`, and webpack folded query-core into the commons
 * chunk that PUBLIC pages load: +11.5 KB and +200 ms of LCP on the SEO
 * landing pages, caught by the Lighthouse CI gate (budget 2500 ms). The
 * banners that consume this hook live in the authenticated layout only —
 * they must never tax the public bundle.
 *
 * `pollWhile` returns the next delay in ms while the condition holds, or
 * `false` to stop; the loop stops by itself once resolved. A failed fetch
 * (session blip) keeps the last known user for the decision instead of
 * killing the loop.
 */
export function useCurrentUser(options?: {
  pollWhile?: (user: CurrentUser | undefined) => number | false;
}) {
  const [user, setUser] = useState<CurrentUser | undefined>(undefined);
  const pollWhileRef = useRef(options?.pollWhile);
  useEffect(() => {
    pollWhileRef.current = options?.pollWhile;
  });

  useEffect(() => {
    let cancelled = false;
    let tid: ReturnType<typeof setTimeout> | null = null;
    let lastKnown: CurrentUser | undefined;

    const tick = async () => {
      try {
        lastKnown = await fetchCurrentUser();
        if (!cancelled) setUser(lastKnown);
      } catch {
        // Anonymous or expired session — keep the last known state; the
        // next server navigation redirects to login anyway.
      }
      if (cancelled) return;
      const delay = pollWhileRef.current?.(lastKnown);
      if (delay) {
        tid = setTimeout(() => void tick(), delay);
      }
    };

    void tick();
    return () => {
      cancelled = true;
      if (tid !== null) clearTimeout(tid);
    };
  }, []);

  return { data: user };
}
