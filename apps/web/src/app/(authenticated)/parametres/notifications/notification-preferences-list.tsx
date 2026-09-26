"use client";

/**
 * Client half of /parametres/notifications — Story 8.2 §AC1.
 *
 * Optimistic per-row toggling: the switch flips immediately, the PUT fires,
 * and on failure the row REVERTS and says so (`role="alert"`). While a PUT
 * is in flight the row's switch is disabled (prevents racing PUTs on the
 * same category) and shows a pending state.
 *
 * RGAA: each switch has a real `<label htmlFor>` (the backend category
 * label), and its state is carried by visible "Activé / Désactivé" text +
 * thumb position — never by colour alone. Keyboard: native input (see
 * `ui/switch.tsx`).
 */
import { useState } from "react";
import { useTranslations } from "next-intl";

import { Switch } from "@/components/ui/switch";
import {
  type NotificationCategory,
  type NotificationPreference,
  updateNotificationPreference,
} from "@/lib/api/notifications";

interface RowState {
  enabled: boolean;
  pending: boolean;
  error: boolean;
}

interface NotificationPreferencesListProps {
  initialPreferences: NotificationPreference[];
}

export function NotificationPreferencesList({
  initialPreferences,
}: NotificationPreferencesListProps) {
  const t = useTranslations("notifications.settings");
  const [rows, setRows] = useState<Record<string, RowState>>(() =>
    Object.fromEntries(
      initialPreferences.map((pref) => [
        pref.category,
        { enabled: pref.enabled, pending: false, error: false },
      ]),
    ),
  );

  const setRow = (category: NotificationCategory, next: RowState) => {
    setRows((prev) => ({ ...prev, [category]: next }));
  };

  const handleToggle = async (category: NotificationCategory, next: boolean) => {
    // Optimistic flip; the switch stays disabled until the PUT settles.
    setRow(category, { enabled: next, pending: true, error: false });
    try {
      const saved = await updateNotificationPreference(category, next);
      setRow(category, { enabled: saved.enabled, pending: false, error: false });
    } catch {
      // Failed PUT: revert the toggle and say so (visible per-row error).
      setRow(category, { enabled: !next, pending: false, error: true });
    }
  };

  return (
    <ul className="flex flex-col divide-y divide-border rounded-lg border border-border bg-bg">
      {initialPreferences.map((pref) => {
        // `noUncheckedIndexedAccess` — the key always exists (state is seeded
        // from the same array), but the type system can't know that.
        const state = rows[pref.category] ?? {
          enabled: pref.enabled,
          pending: false,
          error: false,
        };
        const switchId = `notification-${pref.category}`;
        const errorId = `notification-${pref.category}-error`;
        return (
          <li key={pref.category} className="flex flex-col gap-1 p-4">
            <div className="flex items-center justify-between gap-4">
              <label htmlFor={switchId} className="text-body font-medium text-text">
                {pref.label}
              </label>
              <div className="flex shrink-0 items-center gap-3">
                {/* Visible state text — RGAA: state not conveyed by colour
                    alone. aria-hidden: AT already gets the state from the
                    switch's checked state (avoids double announcement). */}
                <span aria-hidden className="text-body-sm text-text-muted">
                  {state.pending
                    ? t("statePending")
                    : state.enabled
                      ? t("stateEnabled")
                      : t("stateDisabled")}
                </span>
                <Switch
                  id={switchId}
                  checked={state.enabled}
                  disabled={state.pending}
                  aria-describedby={state.error ? errorId : undefined}
                  onChange={(event) => void handleToggle(pref.category, event.target.checked)}
                />
              </div>
            </div>
            {state.error && (
              <p id={errorId} role="alert" className="text-body-sm text-danger">
                {t("updateError")}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
