"use client";

/**
 * "Ta progression" module — Story 8.8 §T1.2.
 *
 * Thin client wrapper: fetches the current user (for `useMaturityLevel`'s
 * query key / enabling) then renders `ProfileMaturityIndicator` tel quel
 * with `variant="dashboard-card"`. No new progression logic — the indicator
 * itself already returns `null` when `level === "complete"` (AC2), and
 * `next_actions` handlers simply navigate to `/profile` (same pattern as
 * `profile-page.tsx`'s edit sheets, kept minimal here since the dashboard
 * card variant does not render the next-actions list itself).
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

  // Code-review fix (Story 8.8): the parent page used to render a
  // `<section aria-labelledby>` unconditionally around this component,
  // producing an empty ARIA landmark whenever this returns `null`
  // (loading, fetch error, or `level === "complete"`). This component now
  // owns its own `<section>` so "no data" means no landmark at all.
  // `level === "complete"` must be checked here too, NOT delegated to
  // `MaturityDashboardCard`'s own `return null` — otherwise this wraps an
  // empty-but-labelled `<section>` around nothing (caught by
  // `ProgressionModule.test.tsx`'s "level is complete" case).
  if (!data || data.level === "complete") return null;

  return (
    <section aria-labelledby="accueil-progression-title">
      <h2 id="accueil-progression-title" className="sr-only">
        Ta progression
      </h2>
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
    </section>
  );
}
