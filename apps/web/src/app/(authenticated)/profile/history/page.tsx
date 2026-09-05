"use client";

import Link from "next/link";
import { useInfiniteQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api/client";

interface HistoryEntry {
  id: string;
  archived_reason: string;
  previous_state: Record<string, unknown>;
  created_at: string;
}

/**
 * Code-review fix (2026-09): same wrong-host bug as `use-student-profile.ts`
 * / `use-maturity-level.ts` — a bare `fetch("/api/v1/...")` resolves against
 * the Next.js dev server, not the Django API, and 404s every time. Fixed
 * proactively here (found while moving this page under `(authenticated)/`
 * for the "profil accessible depuis l'accueil, retour possible" story) —
 * same class of bug, same file family, would have hit the very next click.
 */
async function fetchHistory({ pageParam = 1 }: { pageParam?: number }) {
  return apiFetch<{ results: HistoryEntry[]; next: string | null }>(
    `/api/v1/students/me/profile/history?page=${pageParam}`,
  );
}

const REASON_LABELS: Record<string, string> = {
  major_change_filiere: "Changement de filière",
  major_change_level: "Changement de niveau",
};

export default function ProfileHistoryPage() {
  const { data, fetchNextPage, hasNextPage, isLoading } = useInfiniteQuery({
    queryKey: ["profile-history"],
    queryFn: fetchHistory,
    getNextPageParam: (last) => {
      if (!last.next) return undefined;
      const url = new URL(last.next, "http://localhost");
      const page = Number(url.searchParams.get("page"));
      return Number.isFinite(page) && page > 0 ? page : undefined;
    },
    initialPageParam: 1,
  });

  const entries = data?.pages.flatMap((p) => p.results) ?? [];

  return (
    <main>
      <div className="flex items-center gap-4 border-b p-4">
        <Link href="/profile" className="text-sm">
          ← Mon profil
        </Link>
        <h1 className="text-xl font-semibold">Historique</h1>
      </div>

      <section role="region" aria-label="Historique des changements de profil" className="p-4">
        {isLoading && <p className="text-muted-foreground">Chargement…</p>}

        {!isLoading && entries.length === 0 && (
          <p className="text-sm text-muted-foreground">Aucun changement majeur enregistré.</p>
        )}

        <ol className="space-y-4">
          {entries.map((entry) => (
            <li key={entry.id}>
              <Card className="space-y-2 p-4">
                <p className="text-sm font-medium">
                  {REASON_LABELS[entry.archived_reason] ?? entry.archived_reason}
                </p>
                <p className="text-xs text-muted-foreground">
                  {new Date(entry.created_at).toLocaleDateString("fr-FR", {
                    month: "long",
                    year: "numeric",
                  })}
                </p>
                <Link href={`/profile/history/${entry.id}`} className="text-xs underline">
                  Revoir l&apos;ancien profil
                </Link>
              </Card>
            </li>
          ))}
        </ol>

        {hasNextPage && (
          <Button variant="outline" className="mt-4 w-full" onClick={() => fetchNextPage()}>
            Voir plus
          </Button>
        )}
      </section>
    </main>
  );
}
