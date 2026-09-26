"use client";

/**
 * Modération — Story 9.4. Deux files (motivations élèves 5.5, commentaires
 * écoles P2-5) : texte en pleine largeur, chips de pré-screening (AIDE à
 * prioriser — la décision reste humaine, aucun auto-refus), SLA 24 h
 * ouvrées. Le rejet d'une motivation exige la catégorie typée + un
 * commentaire renvoyé à l'élève (5.5 : il peut corriger et re-soumettre).
 */

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  actOnMotivation,
  actOnSchoolComment,
  fetchPendingMotivations,
  fetchPendingSchoolComments,
  type PendingMotivation,
  type PendingSchoolComment,
  type Prescreen,
} from "@/lib/api/admin-moderation";

const INPUT_CLASS = "w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text";

const REJECT_CATEGORIES = ["contenu_inapproprie", "donnees_tierces", "discrimination", "autre"];

function PrescreenChips({ prescreen }: { prescreen: Prescreen }) {
  const t = useTranslations("admin.moderation");
  if (prescreen.pii.length === 0 && prescreen.risk.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {prescreen.pii.map((kind) => (
        <span
          key={kind}
          className="rounded-full bg-warning-bg px-2 py-0.5 text-xs font-medium text-warning"
        >
          {t("prescreenPii", { kind })}
        </span>
      ))}
      {prescreen.risk.map((word) => (
        <span
          key={word}
          className="rounded-full bg-warning-bg px-2 py-0.5 text-xs font-medium text-warning"
        >
          {t("prescreenRisk")} : {word}
        </span>
      ))}
    </div>
  );
}

function SlaBadge({ hours, overdue }: { hours: number; overdue: boolean }) {
  const t = useTranslations("admin.moderation");
  return (
    <span
      className={
        overdue
          ? "rounded-full bg-warning-bg px-2 py-0.5 text-xs font-medium text-warning"
          : "text-xs text-text-muted"
      }
    >
      {t("age", { hours: Math.round(hours) })}
      {overdue ? ` — ${t("overdue")}` : ""}
    </span>
  );
}

function MotivationCard({ item, onDone }: { item: PendingMotivation; onDone: () => void }) {
  const t = useTranslations("admin.moderation");
  const [rejecting, setRejecting] = useState(false);
  const [category, setCategory] = useState("contenu_inapproprie");
  const [reason, setReason] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const act = async (action: "approve" | "reject") => {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await actOnMotivation(item.id, action, action === "reject" ? { category, reason } : {});
      onDone();
    } catch (err) {
      setError((err as { detail?: string })?.detail ?? t("actionError"));
      setPending(false);
    }
  };

  return (
    <li className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-text">{item.school.name}</span>
        <span className="text-xs text-text-muted">{item.profession_name}</span>
        <span className="text-xs text-text-muted">{item.student_email}</span>
        <SlaBadge hours={item.business_hours_age} overdue={item.overdue} />
      </div>
      <PrescreenChips prescreen={item.prescreen} />
      <blockquote className="whitespace-pre-wrap rounded-lg bg-bg-2 p-3 text-text">
        {item.motivation_text}
      </blockquote>
      {error ? (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : null}
      {rejecting ? (
        <div className="flex flex-col gap-2">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            {t("rejectCategoryLabel")}
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className={INPUT_CLASS}
            >
              {REJECT_CATEGORIES.map((value) => (
                <option key={value} value={value}>
                  {t(`rejectCategories.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            {t("rejectReasonLabel")}
            <textarea
              rows={2}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className={INPUT_CLASS}
            />
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={pending || !reason.trim()}
              onClick={() => void act("reject")}
              className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
            >
              {t("confirmReject")}
            </button>
            <button
              type="button"
              onClick={() => setRejecting(false)}
              className="rounded-lg border border-border px-3 py-1.5 text-xs text-text-muted"
            >
              {t("cancel")}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <button
            type="button"
            disabled={pending}
            onClick={() => void act("approve")}
            className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
          >
            {t("approve")}
          </button>
          <button
            type="button"
            onClick={() => setRejecting(true)}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:bg-bg-2"
          >
            {t("reject")}
          </button>
        </div>
      )}
    </li>
  );
}

function SchoolCommentCard({ item, onDone }: { item: PendingSchoolComment; onDone: () => void }) {
  const t = useTranslations("admin.moderation");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const act = async (action: "approve" | "reject") => {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await actOnSchoolComment(item.id, action);
      onDone();
    } catch {
      setError(t("actionError"));
      setPending(false);
    }
  };

  return (
    <li className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-text">{item.school.name}</span>
        <span className="text-xs text-text-muted">{item.action}</span>
        <SlaBadge hours={item.business_hours_age} overdue={item.overdue} />
      </div>
      <PrescreenChips prescreen={item.prescreen} />
      <blockquote className="whitespace-pre-wrap rounded-lg bg-bg-2 p-3 text-text">
        {item.comment}
      </blockquote>
      {error ? (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : null}
      <div className="flex gap-2">
        <button
          type="button"
          disabled={pending}
          onClick={() => void act("approve")}
          className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
        >
          {t("approveComment")}
        </button>
        <button
          type="button"
          disabled={pending}
          onClick={() => void act("reject")}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:bg-bg-2 disabled:opacity-50"
        >
          {t("rejectComment")}
        </button>
      </div>
    </li>
  );
}

export function ModerationQueues() {
  const t = useTranslations("admin.moderation");
  const [tab, setTab] = useState<"motivations" | "comments">("motivations");
  const [motivations, setMotivations] = useState<PendingMotivation[]>([]);
  const [comments, setComments] = useState<PendingSchoolComment[]>([]);
  const [overdue, setOverdue] = useState({ motivations: 0, comments: 0 });
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setError(false);
    try {
      const [m, c] = await Promise.all([fetchPendingMotivations(), fetchPendingSchoolComments()]);
      setMotivations(m.results);
      setComments(c.results);
      setOverdue({ motivations: m.overdue_count, comments: c.overdue_count });
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    const handle = setTimeout(() => void load(), 0);
    return () => clearTimeout(handle);
  }, [load]);

  return (
    <section aria-labelledby="admin-moderation-title" className="flex flex-col gap-4">
      <h2 id="admin-moderation-title" className="text-xl font-semibold text-text">
        {t("title")}
      </h2>
      <p className="text-xs text-text-muted">{t("humanDecisionNote")}</p>

      <div role="tablist" aria-label={t("title")} className="flex gap-2">
        <button
          role="tab"
          aria-selected={tab === "motivations"}
          onClick={() => setTab("motivations")}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            tab === "motivations"
              ? "bg-primary text-primary-foreground"
              : "border border-border text-text-muted"
          }`}
        >
          {t("tabMotivations", { count: motivations.length })}
          {overdue.motivations > 0 ? ` · ${t("overdueShort", { count: overdue.motivations })}` : ""}
        </button>
        <button
          role="tab"
          aria-selected={tab === "comments"}
          onClick={() => setTab("comments")}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            tab === "comments"
              ? "bg-primary text-primary-foreground"
              : "border border-border text-text-muted"
          }`}
        >
          {t("tabComments", { count: comments.length })}
          {overdue.comments > 0 ? ` · ${t("overdueShort", { count: overdue.comments })}` : ""}
        </button>
      </div>

      {error ? (
        <p role="alert" className="text-body text-danger">
          {t("loadError")}
        </p>
      ) : null}

      {tab === "motivations" ? (
        <ul className="flex flex-col gap-3">
          {motivations.map((item) => (
            <MotivationCard key={item.id} item={item} onDone={() => void load()} />
          ))}
          {motivations.length === 0 ? (
            <li className="text-sm text-text-muted">{t("emptyMotivations")}</li>
          ) : null}
        </ul>
      ) : (
        <ul className="flex flex-col gap-3">
          {comments.map((item) => (
            <SchoolCommentCard key={item.id} item={item} onDone={() => void load()} />
          ))}
          {comments.length === 0 ? (
            <li className="text-sm text-text-muted">{t("emptyComments")}</li>
          ) : null}
        </ul>
      )}
    </section>
  );
}
