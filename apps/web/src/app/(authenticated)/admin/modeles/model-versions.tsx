"use client";

/**
 * Versions du modèle IA — Story 9.5 (art. 22).
 *
 * Liste des versions (hash dataset, hyperparamètres, écart inter-groupes),
 * activation exclusive avec PORTE ÉTHIQUE : un écart > 10 % exige une note
 * de revue avant déploiement — le bouton le dit au lieu de le cacher.
 */

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

interface ModelVersionRow {
  id: string;
  name: string;
  version: string;
  dataset_hash: string;
  hyperparameters: Record<string, number>;
  max_subpopulation_gap: number;
  is_active: boolean;
  requires_ethics_review: boolean;
  ethics_review_note: string;
  deployed_at: string | null;
  deployed_by: string | null;
  decisions_count: number;
}

async function fetchVersions(): Promise<{ versions: ModelVersionRow[] }> {
  return apiFetch("/api/v1/admin/model-versions/");
}

async function activateVersion(id: string, ethicsNote: string) {
  return apiFetch(`/api/v1/admin/model-versions/${id}/activate/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body: ethicsNote ? { ethics_note: ethicsNote } : {},
  });
}

export function ModelVersions() {
  const t = useTranslations("admin.modeles");
  const [versions, setVersions] = useState<ModelVersionRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [noteFor, setNoteFor] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setVersions((await fetchVersions()).versions);
    } catch {
      setError(t("loadError"));
    }
  }, [t]);

  useEffect(() => {
    const handle = setTimeout(() => void load(), 0);
    return () => clearTimeout(handle);
  }, [load]);

  const activate = async (row: ModelVersionRow, ethicsNote: string) => {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await activateVersion(row.id, ethicsNote);
      setNoteFor(null);
      setNote("");
      await load();
    } catch (err) {
      setError((err as { detail?: string })?.detail ?? t("actionError"));
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="admin-modeles-title" className="flex flex-col gap-4">
      <h2 id="admin-modeles-title" className="text-xl font-semibold text-text">
        {t("title")}
      </h2>
      <p className="text-xs text-text-muted">{t("intro")}</p>

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      <ul className="flex flex-col gap-3">
        {versions.map((row) => (
          <li
            key={row.id}
            className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4 text-sm"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-text">{row.version}</span>
              <span className="text-xs text-text-muted">{row.name}</span>
              {row.is_active ? (
                <span className="rounded-full bg-bg-2 px-2 py-0.5 text-xs font-medium text-success">
                  {t("active")}
                </span>
              ) : null}
              {row.requires_ethics_review ? (
                <span className="rounded-full bg-warning-bg px-2 py-0.5 text-xs font-medium text-warning">
                  {t("ethicsRequired", { gap: Math.round(row.max_subpopulation_gap * 100) })}
                </span>
              ) : null}
            </div>
            <p className="font-mono text-xs text-text-muted">
              dataset&nbsp;: {row.dataset_hash.slice(0, 16)}… ·{" "}
              {t("decisions", {
                count: row.decisions_count,
              })}
              {row.deployed_at
                ? ` · ${t("deployedAt", {
                    date: new Date(row.deployed_at).toLocaleDateString("fr-FR"),
                    by: row.deployed_by ?? "—",
                  })}`
                : ""}
            </p>
            <details>
              <summary className="cursor-pointer text-xs text-text-muted">
                {t("hyperparameters")}
              </summary>
              <pre className="mt-1 overflow-x-auto rounded bg-bg-2 p-2 text-xs">
                {JSON.stringify(row.hyperparameters, null, 2)}
              </pre>
            </details>
            {row.ethics_review_note ? (
              <p className="text-xs text-text-muted">
                {t("ethicsNote")} : {row.ethics_review_note}
              </p>
            ) : null}

            {!row.is_active ? (
              noteFor === row.id ? (
                <div className="flex flex-col gap-2">
                  <label className="flex flex-col gap-1 text-xs text-text-muted">
                    {t("ethicsNoteLabel")}
                    <textarea
                      rows={2}
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                      className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={pending || !note.trim()}
                      onClick={() => void activate(row, note)}
                      className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
                    >
                      {t("confirmActivate")}
                    </button>
                    <button
                      type="button"
                      onClick={() => setNoteFor(null)}
                      className="rounded-lg border border-border px-3 py-1.5 text-xs text-text-muted"
                    >
                      {t("cancel")}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  disabled={pending}
                  onClick={() =>
                    row.requires_ethics_review ? setNoteFor(row.id) : void activate(row, "")
                  }
                  className="w-fit rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text hover:bg-bg-2 disabled:opacity-50"
                >
                  {row.requires_ethics_review ? t("activateWithReview") : t("activate")}
                </button>
              )
            ) : null}
          </li>
        ))}
      </ul>
      {versions.length === 0 && !error ? (
        <p className="text-sm text-text-muted">{t("empty")}</p>
      ) : null}
    </section>
  );
}
