"use client";

/**
 * Calendrier Parcoursup — Story 9.2, amendement 8.3 (the visual CRUD the
 * seed command was standing in for). Grouped by campaign; a NOTIFIED
 * milestone (`notified_at` set) is displayed as sent and its date/window
 * are locked — the email left, editing the date would rewrite history.
 */

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  createAdminMilestone,
  fetchAdminMilestones,
  updateAdminMilestone,
  type AdminMilestone,
} from "@/lib/api/admin-schools";

const INPUT_CLASS = "rounded-lg border border-border bg-card px-3 py-2 text-sm text-text";

const KINDS = [
  "ouverture",
  "j30_fermeture_voeux",
  "fermeture_voeux",
  "resultats_principale",
  "resultats_complementaire",
];

export function CalendarAdmin() {
  const t = useTranslations("admin.calendrier");
  const [milestones, setMilestones] = useState<AdminMilestone[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [form, setForm] = useState({
    kind: "ouverture",
    campaign: "",
    date: "",
    notify_days_before: "18",
  });

  const load = useCallback(async () => {
    try {
      setMilestones((await fetchAdminMilestones()).milestones);
    } catch {
      setError(t("loadError"));
    }
  }, [t]);

  useEffect(() => {
    // Deferred initial fetch (react-hooks/set-state-in-effect) — same
    // pattern as the referential tables.
    const handle = setTimeout(() => void load(), 0);
    return () => clearTimeout(handle);
  }, [load]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await createAdminMilestone({
        kind: form.kind,
        campaign: form.campaign,
        date: form.date,
        notify_days_before: Number(form.notify_days_before),
      });
      await load();
    } catch (err) {
      setError((err as { detail?: string })?.detail ?? t("saveError"));
    } finally {
      setPending(false);
    }
  };

  const updateDate = async (milestone: AdminMilestone, date: string) => {
    setError(null);
    try {
      await updateAdminMilestone(milestone.id, { date });
      await load();
    } catch (err) {
      setError((err as { detail?: string })?.detail ?? t("saveError"));
      await load();
    }
  };

  const campaigns = [...new Set(milestones.map((m) => m.campaign))];

  return (
    <section aria-labelledby="admin-calendrier-title" className="flex flex-col gap-6">
      <h2 id="admin-calendrier-title" className="text-xl font-semibold text-text">
        {t("title")}
      </h2>

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      <form onSubmit={(event) => void submit(event)} className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("fields.kind")}
          <select
            value={form.kind}
            onChange={(event) => setForm((f) => ({ ...f, kind: event.target.value }))}
            className={INPUT_CLASS}
          >
            {KINDS.map((kind) => (
              <option key={kind} value={kind}>
                {t(`kinds.${kind}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("fields.campaign")}
          <input
            required
            placeholder="2027-2028"
            value={form.campaign}
            onChange={(event) => setForm((f) => ({ ...f, campaign: event.target.value }))}
            className={INPUT_CLASS}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("fields.date")}
          <input
            required
            type="date"
            value={form.date}
            onChange={(event) => setForm((f) => ({ ...f, date: event.target.value }))}
            className={INPUT_CLASS}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          {t("fields.notifyDaysBefore")}
          <input
            required
            type="number"
            min="0"
            max="60"
            value={form.notify_days_before}
            onChange={(event) => setForm((f) => ({ ...f, notify_days_before: event.target.value }))}
            className={`${INPUT_CLASS} w-24`}
          />
        </label>
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {t("create")}
        </button>
      </form>

      {campaigns.map((campaign) => (
        <div key={campaign} className="flex flex-col gap-2">
          <h3 className="text-lg font-semibold text-text">
            {t("campaign")} {campaign}
          </h3>
          <ul className="flex flex-col gap-2">
            {milestones
              .filter((m) => m.campaign === campaign)
              .map((milestone) => (
                <li
                  key={milestone.id}
                  className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm"
                >
                  <span className="min-w-56 font-medium text-text">{milestone.kind_label}</span>
                  {milestone.notified_at ? (
                    <>
                      <span className="text-text-muted">
                        {new Date(milestone.date).toLocaleDateString("fr-FR")} · J-
                        {milestone.notify_days_before}
                      </span>
                      <span className="rounded-full bg-bg-3 px-2 py-0.5 text-xs text-text-muted">
                        {t("notifiedLocked")}
                      </span>
                    </>
                  ) : (
                    <>
                      <label className="flex items-center gap-2 text-text-muted">
                        {t("fields.date")}
                        <input
                          type="date"
                          defaultValue={milestone.date}
                          onBlur={(event) => {
                            if (event.target.value && event.target.value !== milestone.date) {
                              void updateDate(milestone, event.target.value);
                            }
                          }}
                          className={INPUT_CLASS}
                        />
                      </label>
                      <span className="text-text-muted">J-{milestone.notify_days_before}</span>
                    </>
                  )}
                </li>
              ))}
          </ul>
        </div>
      ))}
      {milestones.length === 0 && !error ? (
        <p className="text-sm text-text-muted">{t("empty")}</p>
      ) : null}
    </section>
  );
}
