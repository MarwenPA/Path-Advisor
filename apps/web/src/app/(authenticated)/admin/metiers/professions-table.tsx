"use client";

/**
 * Back-office professions list — Story 9.1 AC1.
 *
 * Search (name/slug/sector), status filter (publié/brouillon/archivé),
 * sortable name/updated columns, server-side pagination. Reads only —
 * every write lives on the fiche page.
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  fetchAdminProfessions,
  type AdminProfessionList,
  type ProfessionStatus,
} from "@/lib/api/admin-professions";

const STATUS_ORDER: Array<ProfessionStatus | ""> = ["", "published", "draft", "archived"];

function StatusBadge({ status }: { status: ProfessionStatus }) {
  const t = useTranslations("admin.metiers.status");
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

export function ProfessionsTable() {
  const t = useTranslations("admin.metiers");
  const [data, setData] = useState<AdminProfessionList | null>(null);
  const [error, setError] = useState(false);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<ProfessionStatus | "">("");
  const [sort, setSort] = useState("name");
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setError(false);
    try {
      setData(await fetchAdminProfessions({ q, status, sort, page }));
    } catch {
      setError(true);
    }
  }, [q, status, sort, page]);

  useEffect(() => {
    const handle = setTimeout(() => void load(), q ? 250 : 0);
    return () => clearTimeout(handle);
  }, [load, q]);

  const toggleSort = (column: "name" | "updated_at") => {
    setSort((current) => (current === column ? `-${column}` : column));
    setPage(1);
  };

  return (
    <section aria-labelledby="admin-metiers-title" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="admin-metiers-title" className="text-xl font-semibold text-text">
          {t("title")}
          {data ? (
            <span className="ml-2 text-sm font-normal text-text-muted">({data.count})</span>
          ) : null}
        </h2>
        <Link
          href="/admin/metiers/nouveau"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {t("create")}
        </Link>
      </div>

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
            placeholder={t("searchPlaceholder")}
            className="w-64 rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("statusLabel")}
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as ProfessionStatus | "");
              setPage(1);
            }}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-text"
          >
            {STATUS_ORDER.map((value) => (
              <option key={value || "all"} value={value}>
                {value === "" ? t("statusAll") : t(`status.${value}`)}
              </option>
            ))}
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
                <button type="button" onClick={() => toggleSort("name")} className="font-medium">
                  {t("columns.name")} {sort === "name" ? "↑" : sort === "-name" ? "↓" : ""}
                </button>
              </th>
              <th scope="col" className="px-4 py-3">
                {t("columns.sector")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("columns.statusCol")}
              </th>
              <th scope="col" className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSort("updated_at")}
                  className="font-medium"
                >
                  {t("columns.updated")}{" "}
                  {sort === "updated_at" ? "↑" : sort === "-updated_at" ? "↓" : ""}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {(data?.results ?? []).map((profession) => (
              <tr key={profession.id} className="border-b border-border last:border-b-0">
                <td className="px-4 py-3">
                  <Link
                    href={`/admin/metiers/${profession.slug}`}
                    className="font-medium text-primary hover:underline"
                  >
                    {profession.name}
                  </Link>
                  <span className="ml-2 text-xs text-text-muted">{profession.slug}</span>
                </td>
                <td className="px-4 py-3 text-text-muted">{profession.sector || "—"}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={profession.status} />
                </td>
                <td className="px-4 py-3 text-text-muted">
                  {new Date(profession.updated_at).toLocaleDateString("fr-FR")}
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
