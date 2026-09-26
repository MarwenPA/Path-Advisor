"use client";

/**
 * Fiche métier — create/edit form + history panel (Story 9.1 AC2/AC3).
 *
 * The JSON fields (`signals_json`, `requirements_json`, …) are edited as
 * JSON textareas with parse-on-submit: the matching of 8.5/8.6 depends on
 * `signals_json`'s exact shape, and the server re-validates it — this form
 * surfaces the same error instead of silently mangling structures.
 *
 * "Supprimer" is the archive action (story §2.3): the fiche leaves every
 * public surface instantly but history and references survive.
 */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  archiveAdminProfession,
  createAdminProfession,
  fetchProfessionRevisions,
  rollbackAdminProfession,
  updateAdminProfession,
  type AdminProfession,
  type AdminProfessionPayload,
  type ProfessionRevision,
  type ProfessionStatus,
} from "@/lib/api/admin-professions";

const INPUT_CLASS = "w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text";

interface DraftState {
  slug: string;
  name: string;
  description: string;
  daily_routine: string;
  prospects_text: string;
  sector: string;
  rome_code: string;
  median_salary_eur: string;
  status: ProfessionStatus;
  requirements_json: string;
  salary_range_json: string;
  signals_json: string;
  level_compatibility: string;
  sources_json: string;
}

function toDraft(profession: AdminProfession | null): DraftState {
  return {
    slug: profession?.slug ?? "",
    name: profession?.name ?? "",
    description: profession?.description ?? "",
    daily_routine: profession?.daily_routine ?? "",
    prospects_text: profession?.prospects_text ?? "",
    sector: profession?.sector ?? "",
    rome_code: profession?.rome_code ?? "",
    median_salary_eur: profession?.median_salary_eur?.toString() ?? "",
    status: profession?.status ?? "draft",
    requirements_json: JSON.stringify(profession?.requirements_json ?? [], null, 2),
    salary_range_json: JSON.stringify(profession?.salary_range_json ?? null, null, 2),
    signals_json: JSON.stringify(
      profession?.signals_json ?? { passions: [], valeurs: [], specialites: [] },
      null,
      2,
    ),
    level_compatibility: JSON.stringify(profession?.level_compatibility ?? [], null, 2),
    sources_json: JSON.stringify(profession?.sources_json ?? [], null, 2),
  };
}

function toPayload(draft: DraftState): AdminProfessionPayload {
  // Throws SyntaxError on invalid JSON — caught by the submit handler.
  return {
    slug: draft.slug.trim(),
    name: draft.name.trim(),
    description: draft.description,
    daily_routine: draft.daily_routine,
    prospects_text: draft.prospects_text,
    sector: draft.sector.trim(),
    rome_code: draft.rome_code.trim() || null,
    median_salary_eur: draft.median_salary_eur ? Number(draft.median_salary_eur) : null,
    status: draft.status,
    requirements_json: JSON.parse(draft.requirements_json),
    salary_range_json: JSON.parse(draft.salary_range_json),
    signals_json: JSON.parse(draft.signals_json),
    level_compatibility: JSON.parse(draft.level_compatibility),
    sources_json: JSON.parse(draft.sources_json),
  };
}

const ACTION_LABEL_KEY: Record<ProfessionRevision["action"], string> = {
  created: "history.created",
  updated: "history.updated",
  status_changed: "history.statusChanged",
  rolled_back: "history.rolledBack",
};

export function ProfessionForm({ initial }: { initial: AdminProfession | null }) {
  const t = useTranslations("admin.metiers.form");
  const router = useRouter();
  const [draft, setDraft] = useState<DraftState>(() => toDraft(initial));
  const [revisions, setRevisions] = useState<ProfessionRevision[]>([]);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  const isEdit = initial !== null;

  useEffect(() => {
    if (!isEdit) return;
    void fetchProfessionRevisions(initial.slug)
      .then((data) => setRevisions(data.revisions))
      .catch(() => setRevisions([]));
  }, [isEdit, initial?.slug]);

  const set = (field: keyof DraftState) => (value: string) =>
    setDraft((current) => ({ ...current, [field]: value }));

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setFeedback(null);
    try {
      const payload = toPayload(draft);
      if (isEdit) {
        const saved = await updateAdminProfession(initial.slug, payload);
        setFeedback({ tone: "ok", text: t("saved") });
        setRevisions((await fetchProfessionRevisions(saved.slug)).revisions);
        if (saved.slug !== initial.slug) router.replace(`/admin/metiers/${saved.slug}`);
      } else {
        const created = await createAdminProfession(payload);
        router.push(`/admin/metiers/${created.slug}`);
      }
    } catch (error) {
      setFeedback({
        tone: "error",
        text:
          error instanceof SyntaxError
            ? t("invalidJson")
            : ((error as { detail?: string })?.detail ?? t("saveError")),
      });
    } finally {
      setPending(false);
    }
  };

  const archive = async () => {
    if (!isEdit || pending) return;
    setPending(true);
    try {
      await archiveAdminProfession(initial.slug);
      router.push("/admin/metiers");
    } catch {
      setFeedback({ tone: "error", text: t("saveError") });
      setPending(false);
    }
  };

  const rollback = async (revision: ProfessionRevision) => {
    if (!isEdit || pending) return;
    setPending(true);
    setFeedback(null);
    try {
      const restored = await rollbackAdminProfession(initial.slug, revision.id);
      setDraft(toDraft(restored));
      setRevisions((await fetchProfessionRevisions(restored.slug)).revisions);
      setFeedback({ tone: "ok", text: t("rolledBack") });
      if (restored.slug !== initial.slug) router.replace(`/admin/metiers/${restored.slug}`);
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
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.name")}
            <input
              required
              value={draft.name}
              onChange={(event) => set("name")(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.slug")}
            <input
              required
              value={draft.slug}
              onChange={(event) => set("slug")(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.sector")}
            <input
              value={draft.sector}
              onChange={(event) => set("sector")(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.status")}
            <select
              value={draft.status}
              onChange={(event) => set("status")(event.target.value)}
              className={INPUT_CLASS}
            >
              <option value="draft">{t("statusDraft")}</option>
              <option value="published">{t("statusPublished")}</option>
              <option value="archived">{t("statusArchived")}</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.medianSalary")}
            <input
              type="number"
              min="0"
              value={draft.median_salary_eur}
              onChange={(event) => set("median_salary_eur")(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-text-muted">
            {t("fields.romeCode")}
            <input
              value={draft.rome_code}
              onChange={(event) => set("rome_code")(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
        </div>

        {(
          [
            ["description", "fields.description", 4],
            ["daily_routine", "fields.dailyRoutine", 4],
            ["prospects_text", "fields.prospects", 3],
          ] as const
        ).map(([field, labelKey, rows]) => (
          <label key={field} className="flex flex-col gap-1 text-sm text-text-muted">
            {t(labelKey)}
            <textarea
              required
              rows={rows}
              value={draft[field]}
              onChange={(event) => set(field)(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
        ))}

        <details open className="rounded-lg border border-border p-3">
          <summary className="cursor-pointer text-sm font-medium text-text">
            {t("jsonSection")}
          </summary>
          <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
            {(
              [
                ["signals_json", "fields.signals"],
                ["level_compatibility", "fields.levels"],
                ["requirements_json", "fields.requirements"],
                ["salary_range_json", "fields.salaryRange"],
                ["sources_json", "fields.sources"],
              ] as const
            ).map(([field, labelKey]) => (
              <label key={field} className="flex flex-col gap-1 text-sm text-text-muted">
                {t(labelKey)}
                <textarea
                  rows={6}
                  spellCheck={false}
                  value={draft[field]}
                  onChange={(event) => set(field)(event.target.value)}
                  className={`${INPUT_CLASS} font-mono text-xs`}
                />
              </label>
            ))}
          </div>
        </details>

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
        <aside aria-labelledby="revision-history-title" className="flex flex-col gap-3">
          <h3 id="revision-history-title" className="text-lg font-semibold text-text">
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
