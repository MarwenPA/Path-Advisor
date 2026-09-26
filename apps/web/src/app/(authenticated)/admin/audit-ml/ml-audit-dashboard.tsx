"use client";

/**
 * Audit ML — Story 9.6. Lu du journal art. 22 (9.5), calculé à la demande.
 *
 * Formes (dataviz) : tuiles de synthèse (drift KS vs seuil, écart max,
 * baseline), UNE série de barres mensuelles (magnitude, teinte unique du
 * DS, labels directs — pas de légende pour une série), et une TABLE pour
 * les sous-populations (comparer 2-5 groupes se lit mieux en table qu'en
 * barres). Les couleurs de statut (warning) restent réservées aux alertes.
 */

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { apiFetch } from "@/lib/api/client";

interface AuditReport {
  model: {
    version: string;
    deployed_at: string | null;
    baseline_size: number;
    requires_ethics_review: boolean;
  } | null;
  monthly: Array<{ month: string; count: number; mean: number; min: number; max: number }>;
  drift: {
    statistic: number | null;
    threshold: number | null;
    alert: boolean;
    reason?: string;
    n_baseline?: number;
    n_current?: number;
  };
  subpopulations: {
    dimensions: Record<
      string,
      { groups: Record<string, number>; gap: number; counts: Record<string, number> }
    >;
    max_gap: number;
    alert: boolean;
  };
}

function Tile({
  label,
  value,
  alert,
  hint,
}: {
  label: string;
  value: string;
  alert?: boolean;
  hint?: string;
}) {
  return (
    <div className="flex min-w-44 flex-col gap-1 rounded-lg border border-border bg-card px-4 py-3">
      <span className="text-xs uppercase tracking-wide text-text-muted">{label}</span>
      <span
        className={`text-2xl font-semibold tabular-nums ${alert ? "text-warning" : "text-text"}`}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-text-muted">{hint}</span> : null}
    </div>
  );
}

export function MlAuditDashboard() {
  const t = useTranslations("admin.auditMl");
  const [report, setReport] = useState<AuditReport | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setError(false);
    try {
      setReport(await apiFetch<AuditReport>("/api/v1/admin/ml-audit/"));
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    const handle = setTimeout(() => void load(), 0);
    return () => clearTimeout(handle);
  }, [load]);

  if (error) {
    return (
      <p role="alert" className="text-body text-danger">
        {t("loadError")}
      </p>
    );
  }
  if (!report) return <p className="text-sm text-text-muted">{t("loading")}</p>;

  const { drift, subpopulations, monthly, model } = report;
  const maxMean = Math.max(0.0001, ...monthly.map((m) => m.mean));

  return (
    <section aria-labelledby="admin-auditml-title" className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="admin-auditml-title" className="text-xl font-semibold text-text">
          {t("title")}
        </h2>
        {model ? (
          <span className="text-sm text-text-muted">{t("model", { version: model.version })}</span>
        ) : null}
        {drift.alert || subpopulations.alert ? (
          <span className="rounded-full bg-warning-bg px-3 py-1 text-sm font-medium text-warning">
            {t("reviewNeeded")}
          </span>
        ) : (
          <span className="rounded-full bg-bg-2 px-3 py-1 text-sm font-medium text-success">
            {t("healthy")}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <Tile
          label={t("tiles.drift")}
          value={drift.statistic !== null ? `${drift.statistic}` : t("insufficient")}
          alert={drift.alert}
          hint={
            drift.threshold !== null
              ? t("tiles.driftHint", { threshold: drift.threshold })
              : t("tiles.driftFloor")
          }
        />
        <Tile
          label={t("tiles.maxGap")}
          value={`${Math.round(subpopulations.max_gap * 100)} %`}
          alert={subpopulations.alert}
          hint={t("tiles.maxGapHint")}
        />
        <Tile
          label={t("tiles.baseline")}
          value={String(model?.baseline_size ?? 0)}
          hint={t("tiles.baselineHint")}
        />
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold text-text">{t("monthlyTitle")}</h3>
        {monthly.length === 0 ? (
          <p className="text-sm text-text-muted">{t("noData")}</p>
        ) : (
          <div
            role="img"
            aria-label={t("monthlyAria")}
            className="flex items-end gap-3 rounded-lg border border-border bg-card p-4"
            style={{ height: 180 }}
          >
            {monthly.map((bucket) => (
              <div
                key={bucket.month}
                className="flex h-full flex-1 flex-col items-center justify-end gap-1"
              >
                <span className="text-xs tabular-nums text-text-muted">{bucket.mean}</span>
                <div
                  title={`${bucket.month} · ${bucket.count} décisions · moyenne ${bucket.mean}`}
                  className="w-full max-w-12 rounded-t bg-primary"
                  style={{ height: `${Math.max(4, (bucket.mean / maxMean) * 100)}%` }}
                />
                <span className="text-xs text-text-muted">{bucket.month.slice(2)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold text-text">{t("subpopTitle")}</h3>
        <p className="text-xs text-text-muted">{t("subpopNote")}</p>
        {Object.entries(subpopulations.dimensions).map(([dimension, data]) => (
          <div key={dimension} className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full min-w-96 border-collapse bg-card text-sm">
              <caption className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-muted">
                {t(`dimensions.${dimension}`)} — {t("gap")} {Math.round(data.gap * 100)} %
              </caption>
              <thead>
                <tr className="border-b border-border text-left text-text-muted">
                  <th scope="col" className="px-4 py-2">
                    {t("columns.group")}
                  </th>
                  <th scope="col" className="px-4 py-2 text-right">
                    {t("columns.meanScore")}
                  </th>
                  <th scope="col" className="px-4 py-2 text-right">
                    {t("columns.count")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.groups).map(([group, mean]) => (
                  <tr key={group} className="border-b border-border last:border-b-0">
                    <td className="px-4 py-2 text-text">{group}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-text">{mean}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-text-muted">
                      {data.counts[group]}
                    </td>
                  </tr>
                ))}
                {Object.keys(data.groups).length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-3 text-center text-text-muted">
                      {t("groupsTooSmall")}
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      <p className="text-xs text-text-muted">{t("workflowNote")}</p>
    </section>
  );
}
