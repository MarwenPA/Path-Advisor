"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  createGdprExport,
  listGdprExports,
  type GdprExportRequest,
} from "@/lib/api/gdpr";

import { GdprExportCard } from "./gdpr-export-card";

const POLL_INTERVAL_MS = 5_000;

interface State {
  loading: boolean;
  exports: GdprExportRequest[];
  error: string | null;
  submitting: boolean;
}

function hasActiveExport(exports: GdprExportRequest[]): boolean {
  return exports.some(
    (exportRow) =>
      exportRow.status === "pending" || exportRow.status === "in_progress",
  );
}

export function GdprExportList() {
  const [state, setState] = useState<State>({
    loading: true,
    exports: [],
    error: null,
    submitting: false,
  });

  const refresh = useCallback(async () => {
    try {
      const page = await listGdprExports();
      setState((previous) => ({
        ...previous,
        loading: false,
        exports: page.results,
        error: null,
      }));
    } catch (cause) {
      const message =
        cause instanceof ApiError
          ? cause.problem?.detail ?? cause.message
          : "Impossible de récupérer tes demandes d'export pour le moment.";
      setState((previous) => ({ ...previous, loading: false, error: message }));
    }
  }, []);

  // Initial fetch — runs once on mount. `refresh` is async and only calls
  // setState AFTER its `await listGdprExports()` resolves, so the cascading-
  // render warning the rule flags does not apply here.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  // Polling — only active when at least one row is `pending`/`in_progress`.
  // The interval is torn down as soon as no export is active.
  useEffect(() => {
    if (!hasActiveExport(state.exports)) return;
    const interval = setInterval(() => {
      void refresh();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [state.exports, refresh]);

  const requestNewExport = useCallback(async () => {
    setState((previous) => ({ ...previous, submitting: true, error: null }));
    try {
      const created = await createGdprExport();
      setState((previous) => ({
        ...previous,
        submitting: false,
        exports: [created, ...previous.exports],
      }));
    } catch (cause) {
      const message =
        cause instanceof ApiError
          ? cause.problem?.detail ?? cause.message
          : "Impossible de lancer un export pour le moment.";
      setState((previous) => ({
        ...previous,
        submitting: false,
        error: message,
      }));
    }
  }, []);

  if (state.loading) {
    return (
      <p className="text-sm text-text-muted" role="status" aria-live="polite">
        Chargement de tes exports…
      </p>
    );
  }

  const blockedByActive = hasActiveExport(state.exports);

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-col items-start gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-h2 font-semibold text-text">Mes exports</h2>
          <p className="text-sm text-text-muted">
            Lance un nouvel export pour récupérer un ZIP de toutes tes données.
          </p>
        </div>
        <Button
          type="button"
          onClick={requestNewExport}
          disabled={state.submitting || blockedByActive}
          aria-disabled={state.submitting || blockedByActive}
        >
          {state.submitting
            ? "Lancement…"
            : blockedByActive
              ? "Export en cours…"
              : "Demander un export"}
        </Button>
      </div>

      {state.error && (
        <p
          role="alert"
          className="rounded border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          {state.error}
        </p>
      )}

      {state.exports.length === 0 ? (
        <p className="rounded border border-dashed border-border-strong bg-bg-2 px-4 py-8 text-center text-sm text-text-muted">
          Tu n&apos;as encore demandé aucun export. Clique sur «&nbsp;Demander
          un export&nbsp;» pour en lancer un.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {state.exports.map((exportRow) => (
            <li key={exportRow.id}>
              <GdprExportCard
                export_={exportRow}
                onRetry={
                  exportRow.status === "failed" ? requestNewExport : undefined
                }
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
