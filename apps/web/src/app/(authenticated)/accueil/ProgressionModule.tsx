"use client";

/**
 * "Ta progression" content — Story 8.8 §T1.2.
 *
 * Thin client wrapper: fetches the current user (for `useMaturityLevel`'s
 * query key / enabling) then renders `ProfileMaturityIndicator` tel quel
 * with `variant="dashboard-card"`. No new progression logic — the indicator
 * itself already returns `null` when `level === "complete"` (AC2), and
 * `next_actions` handlers simply navigate to `/profile` (same pattern as
 * `profile-page.tsx`'s edit sheets, kept minimal here since the dashboard
 * card variant does not render the next-actions list itself).
 *
 * Code-review note (2026-09-05, "mets le bloc Tes paris dans Ta
 * progression"): this used to own its own `<section>`/`<Card>` — now it's
 * nested INSIDE the single "Ta progression" card that `page.tsx` renders
 * (which also contains "Tes paris"), so it only returns the indicator
 * itself (or `null`), no wrapping landmark/heading of its own — the parent
 * Card's `<h2 id="accueil-progression-title">` is the one and only heading
 * for this whole card, `ProfileMaturityIndicator`'s own `aria-label` on its
 * root div is enough for the indicator itself to stay identifiable to
 * assistive tech without a nested landmark.
 */
import { useEffect, useState } from "react";

import { ProfileMaturityIndicator } from "@/components/features/profile/profile-maturity-indicator";
import { useMaturityLevel } from "@/hooks/use-maturity-level";
import { fetchCurrentUser, type CurrentUser } from "@/lib/api/auth";

export function ProgressionModule() {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCurrentUser()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        // Authenticated layout already guarantees a logged-in user reaches
        // this page — a failure here just means the module stays hidden.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { data } = useMaturityLevel(user?.id);

  if (!data || data.level === "complete") return null;

  return (
    <ProfileMaturityIndicator
      variant="dashboard-card"
      level={data.level}
      nextActions={data.next_actions.map((action) => ({
        ...action,
        onClick: () => {
          window.location.href = "/profile";
        },
      }))}
    />
  );
}
