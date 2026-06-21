"use client";

/**
 * useFavoriteSchool — optimistic favorite toggle for a school.
 *
 * Story 4.8: wraps POST/DELETE /api/v1/schools/{slug}/favorite/ with
 * useTransition so React can keep the UI interactive during the async call.
 * On network error the local state is reverted so the button stays consistent.
 *
 * Design notes:
 * - The optimistic flip (`setFavorited(nextFavorited)`) happens *before*
 *   startTransition so the UI responds immediately.
 * - The revert uses a functional updater `(prev) => !prev` rather than the
 *   captured `nextFavorited` value. This avoids a stale-closure bug if the
 *   component re-renders between the API call and the catch handler.
 * - useTransition is appropriate here: it marks the API confirmation as
 *   non-blocking, keeps `isPending` true until the network round-trip
 *   completes, and allows React to batch concurrent state updates.
 */

import { useState, useTransition } from "react";
import { apiFetch } from "@/lib/api/client";

export function useFavoriteSchool(schoolSlug: string, initialFavorited = false) {
  const [favorited, setFavorited] = useState(initialFavorited);
  const [isPending, startTransition] = useTransition();

  function toggle() {
    // Optimistic update: flip state immediately before the async work starts.
    const nextFavorited = !favorited;
    setFavorited(nextFavorited);

    startTransition(async () => {
      try {
        if (nextFavorited) {
          await apiFetch(`/api/v1/schools/${schoolSlug}/favorite/`, { method: "POST" });
        } else {
          await apiFetch(`/api/v1/schools/${schoolSlug}/favorite/`, { method: "DELETE" });
        }
      } catch {
        // Revert on error using functional updater to avoid stale-closure issues
        // (the caught error may arrive after further re-renders).
        setFavorited((prev) => !prev);
      }
    });
  }

  return { favorited, toggle, isPending };
}
