"use client";

/**
 * Fiche école — create/edit + history/rollback (Story 9.2, mirror of the
 * 9.1 profession form). Scalar fields only in the MVP form; the JSON
 * columns (dates parcoursup/affelnet, top_debouches) stay editable via a
 * single JSON section like 9.1.
 */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  archiveAdminSchool,
  createAdminSchool,
  fetchSchoolRevisions,
  rollbackAdminSchool,
  updateAdminSchool,
  type AdminSchool,
  type SchoolRevision,
} from "@/lib/api/admin-schools";

const INPUT_CLASS = "w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text";

const SCALAR_FIELDS = [
  ["name", "text"],
  ["slug", "text"],
  ["type", "text"],
  ["city", "text"],
  ["region", "text"],
  ["postal_code", "text"],
  ["public_private", "text"],
  ["selectivity_index", "number"],
  ["official_url", "url"],
] as const;

const ACTION_LABEL_KEY: Record<SchoolRevision["action"], string> = {
  created: "history.created",
  updated: "history.updated",
  status_changed: "history.statusChanged",
  rolled_back: "history.rolledBack",
  imported: "history.imported",
};

export function SchoolForm({ initial }: { initial: AdminSchool | null }) {
  const t = useTranslations("admin.ecoles.form");
  const router = useRouter();
  const isEdit = initial !== null;
  const [draft, setDraft] = useState<Record<string, string>>(() => ({
    name: initial?.name ?? "",
    slug: initial?.slug ?? "",
    type: initial?.type ?? "bts",
    city: initial?.city ?? "",
    region: initial?.region ?? "",
    postal_code: initial?.postal_code ?? "",
    public_private: initial?.public_private ?? "public",
    selectivity_index: String(initial?.selectivity_index ?? 3),
    official_url: initial?.official_url ?? "",
    description: initial?.description ?? "",
    status: initial?.status ?? "draft",
  }));
  const [revisions, setRevisions] = useState<SchoolRevision[]>([]);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!isEdit) return;
    void fetchSchoolRevisions(initial.slug)
      .then((data) => setRevisions(data.revisions))
      .catch(() => setRevisions([]));
  }, [isEdit, initial?.slug]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setFeedback(null);
    const payload = { ...draft, selectivity_index: Number(draft.selectivity_index) };
    try {
      if (isEdit) {
        const saved = await updateAdminSchool(initial.slug, payload);
        setFeedback({ tone: "ok", text: t("saved") });
        setRevisions((await fetchSchoolRevisions(saved.slug)).revisions);
        if (saved.slug !== initial.slug) router.replace(`/admin/ecoles/${saved.slug}`);
      } else {
        const created = await createAdminSchool(payload);
        router.push(`/admin/ecoles/${created.slug}`);
      }
    } catch {
      setFeedback({ tone: "error", text: t("saveError") });
    } finally {
      setPending(false);
    }
  };

  const archive = async () => {
    if (!isEdit || pending) return;
    setPending(true);
    try {
      await archiveAdminSchool(initial.slug);
      router.push("/admin/ecoles");
    } catch {
      setFeedback({ tone: "error", text: t("saveError") });
      setPending(false);
    }
  };

  const rollback = async (revision: SchoolRevision) => {
    if (!isEdit || pending) return;
    setPending(true);
    setFeedback(null);
    try {
      const restored = await rollbackAdminSchool(initial.slug, revision.id);
      setDraft((current) => ({
        ...current,
        ...Object.fromEntries(
          Object.entries(restored).filter(([key]) => key in current) as Array<[string, string]>,
        ),
        selectivity_index: String(restored.selectivity_index),
      }));
      setRevisions((await fetchSchoolRevisions(restored.slug)).revisions);
      setFeedback({ tone: "ok", text: t("rolledBack") });
      if (restored.slug !== initial.slug) router.replace(`/admin/ecoles/${restored.slug}`);
    } catch {
      setFeedback({ tone: "error", text: t("saveError") });
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[2fr_1fr]">
      <form onSubmit={(event) => void submit(event)} className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold text-text">
          {isEdit ? t("editTitle", { name: initial.name }) : t("createTitle")}
        </h2>

        {feedback ? (
          <p
            role={feedback.tone === "error" ? "alert" : "status"}
            className={feedback.tone === "error" ? "text-sm text-danger" : "text-sm text-success"}
          >
            {feedback.text}
          </p>
        ) : null}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {SCALAR_FIELDS.map(([field, kind]) => (
            <label key={field} className="flex flex-col gap-1 text-sm text-text-muted">
              {t(`fields.${field}`)}
              <input
                required={field !== "official_url"}
                type={kind}
                value={draft[field] ?? ""}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, [field]: event.target.value }))
                }
                className={INPUT_CLASS}
              />
            </label>
          ))}
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.status")}
            <select
              value={draft.status}
              onChange={(event) =>
                setDraft((current) => ({ ...current, status: event.target.value }))
              }
              className={INPUT_CLASS}
            >
              <option value="draft">{t("statusDraft")}</option>
              <option value="published">{t("statusPublished")}</option>
              <option value="archived">{t("statusArchived")}</option>
            </select>
          </label>
        </div>

        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("fields.description")}
          <textarea
            rows={4}
            value={draft.description}
            onChange={(event) =>
              setDraft((current) => ({ ...current, description: event.target.value }))
            }
            className={INPUT_CLASS}
          />
        </label>

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={pending}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isEdit ? t("save") : t("createSubmit")}
          </button>
          {isEdit && initial.status !== "archived" ? (
            <button
              type="button"
              disabled={pending}
              onClick={() => void archive()}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:bg-bg-2 disabled:opacity-50"
            >
              {t("archive")}
            </button>
          ) : null}
        </div>
      </form>

      {isEdit ? (
        <aside aria-labelledby="school-history-title" className="flex flex-col gap-3">
          <h3 id="school-history-title" className="text-lg font-semibold text-text">
            {t("history.title")}
          </h3>
          <ol className="flex flex-col gap-2">
            {revisions.map((revision, index) => (
              <li
                key={revision.id}
                className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-text">
                    {t(ACTION_LABEL_KEY[revision.action])}
                  </span>
                  <time className="text-xs text-text-muted">
                    {new Date(revision.created_at).toLocaleString("fr-FR")}
                  </time>
                </div>
                <p className="text-xs text-text-muted">{revision.editor_email ?? "—"}</p>
                {index > 0 ? (
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => void rollback(revision)}
                    className="mt-1 text-xs font-medium text-primary hover:underline disabled:opacity-50"
                  >
                    {t("history.rollback")}
                  </button>
                ) : null}
              </li>
            ))}
            {revisions.length === 0 ? (
              <li className="text-sm text-text-muted">{t("history.empty")}</li>
            ) : null}
          </ol>
        </aside>
      ) : null}
    </div>
  );
}
