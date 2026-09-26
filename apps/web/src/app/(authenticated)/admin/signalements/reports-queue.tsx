"use client";

/**
 * File de signalements — Story 9.3.
 *
 * Oldest first (SLA 7 j) : chaque ligne porte son âge + le badge « > 7 j »
 * et la tête de file affiche le compteur d'alertes. Trois actions par
 * signalement : corriger (lien direct fiche 9.1), rejeter (motif requis),
 * demander des précisions (message requis, notifié à l'élève).
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  actOnReport,
  fetchAdminReports,
  type AdminReport,
  type AdminReportList,
} from "@/lib/api/admin-reports";

const INPUT_CLASS = "w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text";

function ageInDays(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}

function ReportRow({
  report,
  onDone,
}: {
  report: AdminReport & { profession_slug?: string; profession_name?: string };
  onDone: () => void;
}) {
  const t = useTranslations("admin.signalements");
  const [mode, setMode] = useState<"idle" | "dismiss" | "info">("idle");
  const [text, setText] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const slug = report.profession_slug ?? report.profession?.slug ?? "";
  const name = report.profession_name ?? report.profession?.name ?? slug;

  const act = async (action: "resolve" | "dismiss" | "request-info") => {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await actOnReport(report.id, action, {
        note: action === "resolve" ? text : undefined,
        reason: action === "dismiss" ? text : undefined,
        message: action === "request-info" ? text : undefined,
      });
      onDone();
    } catch (err) {
      setError((err as { detail?: string })?.detail ?? t("actionError"));
      setPending(false);
    }
  };

  return (
    <li className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-text">{name}</span>
        <span className="text-xs text-text-muted">{report.error_type_label}</span>
        <span className="text-xs text-text-muted">
          {t("age", { days: ageInDays(report.created_at) })}
        </span>
        {report.overdue ? (
          <span className="rounded-full bg-warning-bg px-2 py-0.5 text-xs font-medium text-warning">
            {t("overdue")}
          </span>
        ) : null}
        {report.status === "info_requested" ? (
          <span className="rounded-full bg-bg-3 px-2 py-0.5 text-xs text-text-muted">
            {t("infoRequested")}
          </span>
        ) : null}
      </div>

      {report.comment ? <p className="text-text-muted">« {report.comment} »</p> : null}
      {report.location ? (
        <p className="text-xs text-text-muted">
          {t("location")} : {report.location}
        </p>
      ) : null}

      {error ? (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : null}

      {mode === "idle" ? (
        <div className="flex flex-wrap gap-2">
          <Link
            href={`/admin/metiers/${slug}`}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text hover:bg-bg-2"
          >
            {t("fixFiche")}
          </Link>
          <button
            type="button"
            disabled={pending}
            onClick={() => void act("resolve")}
            className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {t("resolve")}
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("dismiss");
              setText("");
            }}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:bg-bg-2"
          >
            {t("dismiss")}
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("info");
              setText("");
            }}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:bg-bg-2"
          >
            {t("requestInfo")}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            {mode === "dismiss" ? t("dismissReasonLabel") : t("infoMessageLabel")}
            <textarea
              rows={2}
              value={text}
              onChange={(event) => setText(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={pending || !text.trim()}
              onClick={() => void act(mode === "dismiss" ? "dismiss" : "request-info")}
              className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
            >
              {t("confirm")}
            </button>
            <button
              type="button"
              onClick={() => setMode("idle")}
              className="rounded-lg border border-border px-3 py-1.5 text-xs text-text-muted"
            >
              {t("cancel")}
            </button>
          </div>
        </div>
      )}
    </li>
  );
}

export function ReportsQueue() {
  const t = useTranslations("admin.signalements");
  const [data, setData] = useState<AdminReportList | null>(null);
  const [errorType, setErrorType] = useState("");
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setError(false);
    try {
      setData(await fetchAdminReports({ error_type: errorType }));
    } catch {
      setError(true);
    }
  }, [errorType]);

  useEffect(() => {
    const handle = setTimeout(() => void load(), 0);
    return () => clearTimeout(handle);
  }, [load]);

  return (
    <section aria-labelledby="admin-signalements-title" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="admin-signalements-title" className="text-xl font-semibold text-text">
          {t("title")}
          {data ? (
            <span className="ml-2 text-sm font-normal text-text-muted">({data.count})</span>
          ) : null}
        </h2>
        {data && data.overdue_count > 0 ? (
          <span
            role="status"
            className="rounded-full bg-warning-bg px-3 py-1 text-sm font-medium text-warning"
          >
            {t("overdueBanner", { count: data.overdue_count })}
          </span>
        ) : null}
      </div>

      <label className="flex w-fit flex-col gap-1 text-sm text-text-muted">
        {t("typeLabel")}
        <select
          value={errorType}
          onChange={(event) => setErrorType(event.target.value)}
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
        >
          <option value="">{t("allTypes")}</option>
          <option value="description_inexacte">{t("types.description_inexacte")}</option>
          <option value="debouches_perimes">{t("types.debouches_perimes")}</option>
          <option value="lien_casse">{t("types.lien_casse")}</option>
          <option value="autre">{t("types.autre")}</option>
        </select>
      </label>

      {error ? (
        <p role="alert" className="text-body text-danger">
          {t("loadError")}
        </p>
      ) : null}

      <ul className="flex flex-col gap-3">
        {(data?.results ?? []).map((report) => (
          <ReportRow key={report.id} report={report} onDone={() => void load()} />
        ))}
      </ul>
      {data && data.results.length === 0 ? (
        <p className="text-sm text-text-muted">{t("empty")}</p>
      ) : null}
    </section>
  );
}
