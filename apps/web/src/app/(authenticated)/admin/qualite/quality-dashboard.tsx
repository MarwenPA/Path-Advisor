"use client";

/**
 * Qualité référentiel — Story 10.3 (FR-FF3). Lu de
 * `/api/v1/admin/referential-quality/`, calculé à la demande côté API.
 *
 * Formes (dataviz, patron 9.6) : tuiles de synthèse (couverture vs cibles
 * FR48, fraîcheur 12 mois, files ouvertes), UNE série de barres par
 * tendance (teinte unique, labels directs), couleurs de statut réservées
 * aux alertes. Chaque KPI de file porte son CTA vers la file à traiter
 * (AC : « un CTA me redirige vers la file »).
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { apiFetch } from "@/lib/api/client";

interface QualityReport {
  professions: Record<string, number> & { targets: { mvp: number; growth: number } };
  schools: Record<string, number> & { targets: { mvp: number; growth: number } };
  freshness: {
    window_days: number;
    threshold_pct: number;
    professions_pct: number | null;
    schools_pct: number | null;
    alert: boolean;
  };
  reports: { open: number; overdue: number; threshold: number; alert: boolean };
  moderation: { motivations_pending: number; school_comments_pending: number };
  trends: {
    months: string[];
    profession_edits: number[];
    school_edits: number[];
    reports_opened: number[];
  };
}

function Tile({
  label,
  value,
  alert,
  hint,
  ctaHref,
  ctaLabel,
}: {
  label: string;
  value: string;
  alert?: boolean;
  hint?: string;
  ctaHref?: string;
  ctaLabel?: string;
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
      {ctaHref && ctaLabel ? (
        <Link href={ctaHref} className="text-xs font-medium text-primary hover:underline">
          {ctaLabel}
        </Link>
      ) : null}
    </div>
  );
}

function TrendBars({ months, values, aria }: { months: string[]; values: number[]; aria: string }) {
  const max = Math.max(1, ...values);
  return (
    <div
      role="img"
      aria-label={aria}
      className="flex items-end gap-3 rounded-lg border border-border bg-card p-4"
      style={{ height: 140 }}
    >
      {months.map((month, i) => (
        <div key={month} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
          <span className="text-xs tabular-nums text-text-muted">{values[i]}</span>
          <div
            title={`${month} · ${values[i]}`}
            className="w-full max-w-12 rounded-t bg-primary"
            style={{ height: `${Math.max(4, ((values[i] ?? 0) / max) * 100)}%` }}
          />
          <span className="text-xs text-text-muted">{month.slice(2)}</span>
        </div>
      ))}
    </div>
  );
}

export function QualityDashboard() {
  const t = useTranslations("admin.qualite");
  const [report, setReport] = useState<QualityReport | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setError(false);
    try {
      setReport(await apiFetch<QualityReport>("/api/v1/admin/referential-quality/"));
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

  const { professions, schools, freshness, reports, moderation, trends } = report;
  const anyAlert = freshness.alert || reports.alert;

  const pct = (value: number | null) => (value === null ? t("noData") : `${value} %`);

  return (
    <section aria-labelledby="admin-qualite-title" className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="admin-qualite-title" className="text-xl font-semibold text-text">
          {t("title")}
        </h2>
        {anyAlert ? (
          <span className="rounded-full bg-warning-bg px-3 py-1 text-sm font-medium text-warning">
            {t("attentionNeeded")}
          </span>
        ) : (
          <span className="rounded-full bg-bg-2 px-3 py-1 text-sm font-medium text-success">
            {t("healthy")}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <Tile
          label={t("tiles.professions")}
          value={`${professions.published} / ${professions.targets.mvp}`}
          hint={t("tiles.professionsHint", {
            draft: professions.draft ?? 0,
            growth: professions.targets.growth,
          })}
          ctaHref="/admin/metiers"
          ctaLabel={t("tiles.manage")}
        />
        <Tile
          label={t("tiles.schools")}
          value={`${schools.published} / ${schools.targets.mvp}`}
          hint={t("tiles.schoolsHint", {
            draft: schools.draft ?? 0,
            growth: schools.targets.growth,
          })}
          ctaHref="/admin/ecoles"
          ctaLabel={t("tiles.manage")}
        />
        <Tile
          label={t("tiles.freshness")}
          value={pct(freshness.professions_pct)}
          alert={freshness.alert}
          hint={t("tiles.freshnessHint", {
            schools: pct(freshness.schools_pct),
            threshold: freshness.threshold_pct,
          })}
        />
        <Tile
          label={t("tiles.reports")}
          value={String(reports.open)}
          alert={reports.alert}
          hint={t("tiles.reportsHint", { overdue: reports.overdue, threshold: reports.threshold })}
          ctaHref="/admin/signalements"
          ctaLabel={t("tiles.goToQueue")}
        />
        <Tile
          label={t("tiles.moderation")}
          value={String(moderation.motivations_pending + moderation.school_comments_pending)}
          hint={t("tiles.moderationHint", {
            motivations: moderation.motivations_pending,
            comments: moderation.school_comments_pending,
          })}
          ctaHref="/admin/moderation"
          ctaLabel={t("tiles.goToQueue")}
        />
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold text-text">{t("trendEditsTitle")}</h3>
        <TrendBars
          months={trends.months}
          values={trends.profession_edits}
          aria={t("trendEditsAria")}
        />
      </div>
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold text-text">{t("trendSchoolsTitle")}</h3>
        <TrendBars
          months={trends.months}
          values={trends.school_edits}
          aria={t("trendSchoolsAria")}
        />
      </div>
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold text-text">{t("trendReportsTitle")}</h3>
        <TrendBars
          months={trends.months}
          values={trends.reports_opened}
          aria={t("trendReportsAria")}
        />
      </div>
    </section>
  );
}
