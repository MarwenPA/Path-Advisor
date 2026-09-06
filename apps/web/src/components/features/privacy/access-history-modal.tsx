"use client";

/**
 * <AccessHistoryModal> — "Voir l'historique d'accès" (Story 6.11 AC).
 *
 * A lightweight, dependency-free dialog (no headless-ui/radix installed
 * for this surface elsewhere in the app) — opened from `<TierAccessCard>`,
 * fetches the 90-day log lazily on open.
 */
import { useEffect, useState } from "react";

import { fetchAccessHistory, buildAccessHistoryExportUrl } from "@/lib/api/access-list";
import { ACCESS_LIST_COPY } from "@/lib/i18n/fr/access-list";

export function AccessHistoryModal({ entryId, onClose }: { entryId: string; onClose: () => void }) {
  const [history, setHistory] = useState<{ consulted_at: string }[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchAccessHistory(entryId)
      .then((res) => {
        if (!cancelled) setHistory(res.results);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [entryId]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="access-history-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div className="w-full max-w-md rounded-lg bg-bg p-6 shadow-lg">
        <h2 id="access-history-title" className="mb-4 text-h3 font-semibold text-text">
          {ACCESS_LIST_COPY.historyModalTitle}
        </h2>

        {error ? (
          <p className="text-body-sm text-danger">Impossible de charger l&apos;historique.</p>
        ) : history === null ? (
          <p className="text-body-sm text-text-muted">Chargement…</p>
        ) : history.length === 0 ? (
          <p className="text-body-sm text-text-muted">{ACCESS_LIST_COPY.historyEmptyState}</p>
        ) : (
          <ul className="flex max-h-64 flex-col gap-1 overflow-y-auto text-body-sm text-text">
            {history.map((row, i) => (
              <li key={i} className="border-b border-border py-1">
                {new Date(row.consulted_at).toLocaleString("fr-FR")}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-4 flex justify-between gap-2">
          <a
            href={buildAccessHistoryExportUrl(entryId)}
            className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-card"
          >
            {ACCESS_LIST_COPY.historyExportCsvLabel}
          </a>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-primary px-3 py-1.5 text-body-sm font-medium text-primary-foreground"
          >
            {ACCESS_LIST_COPY.historyCloseLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
