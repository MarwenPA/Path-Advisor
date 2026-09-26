"use client";

/**
 * Back-office schools list + CSV import — Story 9.2 AC1/AC2.
 *
 * The import block posts the file, then renders the drill-down report:
 * created (drafts), conflicts (existing vs incoming, link to the fiche for
 * MANUAL resolution — the AC's contract, never an auto-merge) and per-line
 * validation errors.
 */

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";

import {
  fetchAdminSchools,
  importSchoolsCsv,
  type AdminSchoolList,
  type CsvImportReport,
} from "@/lib/api/admin-schools";

const SCHOOL_TYPES = ["lycee_pro", "prepa", "bts", "iut", "ecole_ingenieur", "ecole_commerce"];

function StatusBadge({ status }: { status: string }) {
  const t = useTranslations("admin.ecoles.status");
  const tone =
    status === "published"
      ? "bg-bg-2 text-success"
      : status === "draft"
        ? "bg-warning-bg text-warning"
        : "bg-bg-3 text-text-muted";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${tone}`}>
      {t(status)}
    </span>
  );
}

export function SchoolsTable() {
  const t = useTranslations("admin.ecoles");
  const [data, setData] = useState<AdminSchoolList | null>(null);
  const [error, setError] = useState(false);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [region, setRegion] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [report, setReport] = useState<CsvImportReport | null>(null);
  const [importing, setImporting] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setError(false);
    try {
      setData(await fetchAdminSchools({ q, type, region, status: statusFilter, page }));
    } catch {
      setError(true);
    }
  }, [q, type, region, statusFilter, page]);

  useEffect(() => {
    const handle = setTimeout(() => void load(), q || region ? 250 : 0);
    return () => clearTimeout(handle);
  }, [load, q, region]);

  const runImport = async (file: File) => {
    setImporting(true);
    setReport(null);
    try {
      const result = await importSchoolsCsv(file);
      setReport(result);
      void load();
    } catch {
      setError(true);
    } finally {
      setImporting(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  return (
    <section aria-labelledby="admin-ecoles-title" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="admin-ecoles-title" className="text-xl font-semibold text-text">
          {t("title")}
          {data ? (
            <span className="ml-2 text-sm font-normal text-text-muted">({data.count})</span>
          ) : null}
        </h2>
        <div className="flex flex-wrap gap-2">
          <label className="cursor-pointer rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-text hover:bg-bg-2">
            {importing ? t("importing") : t("importCsv")}
            <input
              ref={fileInput}
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              disabled={importing}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void runImport(file);
              }}
            />
          </label>
          <Link
            href="/admin/ecoles/nouvelle"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            {t("create")}
          </Link>
        </div>
      </div>

      <p className="text-xs text-text-muted">{t("csvHint")}</p>

      {report ? (
        <div
          role="status"
          className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4 text-sm"
        >
          <p className="font-medium text-text">
            {t("report.summary", {
              created: report.created.length,
              conflicts: report.conflicts.length,
              errors: report.errors.length,
            })}
          </p>
          {report.created.length > 0 ? (
            <p className="text-text-muted">{t("report.createdAsDrafts")}</p>
          ) : null}
          {report.conflicts.map((conflict) => (
            <p key={conflict.slug} className="text-text-muted">
              {t("report.conflictLine", { line: conflict.line, slug: conflict.slug })}{" "}
              <span className="text-xs">
                ({t("report.existing")} : {conflict.existing.name} — {t("report.incoming")} :{" "}
                {conflict.incoming.name})
              </span>{" "}
              <Link
                href={`/admin/ecoles/${conflict.slug}`}
                className="font-medium text-primary hover:underline"
              >
                {t("report.resolve")}
              </Link>
            </p>
          ))}
          {report.errors.map((line) => (
            <p key={line.line} className="text-danger">
              {t("report.errorLine", { line: line.line })} — {JSON.stringify(line.errors)}
            </p>
          ))}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("searchLabel")}
          <input
            type="search"
            value={q}
            onChange={(event) => {
              setQ(event.target.value);
              setPage(1);
            }}
            className="w-56 rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("typeLabel")}
          <select
            value={type}
            onChange={(event) => {
              setType(event.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
          >
            <option value="">{t("allTypes")}</option>
            {SCHOOL_TYPES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("regionLabel")}
          <input
            value={region}
            onChange={(event) => {
              setRegion(event.target.value);
              setPage(1);
            }}
            className="w-44 rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("statusLabel")}
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
          >
            <option value="">{t("allStatuses")}</option>
            <option value="published">{t("status.published")}</option>
            <option value="draft">{t("status.draft")}</option>
            <option value="archived">{t("status.archived")}</option>
          </select>
        </label>
      </div>

      {error ? (
        <p role="alert" className="text-body text-danger">
          {t("loadError")}
        </p>
      ) : null}

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full min-w-[640px] border-collapse bg-card text-sm">
          <thead>
            <tr className="border-b border-border text-left text-text-muted">
              <th scope="col" className="px-4 py-3">
                {t("columns.name")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("columns.type")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("columns.region")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("columns.statusCol")}
              </th>
            </tr>
          </thead>
          <tbody>
            {(data?.results ?? []).map((school) => (
              <tr key={school.id} className="border-b border-border last:border-b-0">
                <td className="px-4 py-3">
                  <Link
                    href={`/admin/ecoles/${school.slug}`}
                    className="font-medium text-primary hover:underline"
                  >
                    {school.name}
                  </Link>
                  <span className="ml-2 text-xs text-text-muted">{school.city}</span>
                </td>
                <td className="px-4 py-3 text-text-muted">{school.type}</td>
                <td className="px-4 py-3 text-text-muted">{school.region}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={school.status} />
                </td>
              </tr>
            ))}
            {data && data.results.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-text-muted">
                  {t("empty")}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {data && (data.previous || data.next) ? (
        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={!data.previous}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            className="rounded-lg border border-border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            {t("previous")}
          </button>
          <button
            type="button"
            disabled={!data.next}
            onClick={() => setPage((current) => current + 1)}
            className="rounded-lg border border-border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            {t("next")}
          </button>
        </div>
      ) : null}
    </section>
  );
}
