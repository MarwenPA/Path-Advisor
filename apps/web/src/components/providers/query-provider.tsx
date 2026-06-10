"use client";

import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * `<QueryProvider>` — wraps the app in a single TanStack Query client.
 *
 * Story 2.1 is the first consumer (onboarding GET + PATCH); future
 * stories (3.x recommendations, 4.x graph, 6.x espaces tiers) will
 * share the same client. Mounting at the root layout means every
 * page benefits from request deduplication + cache without re-wrapping.
 *
 * `useState` ensures the client is created exactly once per browser
 * session (Next.js streams chunks across server / client; constructing
 * the client in the module scope would share it across users on the
 * server-side stream — `useState(() => new QueryClient())` is the
 * canonical Next.js + TanStack pattern).
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // 30s stale — most snapshot endpoints in this app are
            // user-scoped and rarely invalidated by other tabs.
            staleTime: 30_000,
            // No retry on 4xx (auth, validation). Retry once on 5xx
            // / network for transient blips.
            retry: (failureCount, error) => {
              const status = (error as { status?: number } | null)?.status;
              if (status !== undefined && status >= 400 && status < 500) return false;
              return failureCount < 1;
            },
            refetchOnWindowFocus: false,
          },
        },
      }),
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
