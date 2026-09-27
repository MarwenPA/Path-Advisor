/**
 * API fetchers for notification preferences — Story 8.2.
 *
 * Two surfaces (mirroring `apps/api/apps/notifications/views.py`):
 *   - Authenticated `GET/PUT /api/v1/me/notification-preferences/` — the
 *     `/parametres/notifications` settings page. PUT saves immediately per
 *     category (AC1 — no "save" button), so it carries the CSRF token like
 *     every other authenticated mutation.
 *   - Public `POST /api/v1/notifications/unsubscribe/` — the email footer
 *     link's target. Anonymous, token-in-body; the backend declares
 *     `authentication_classes = []` so no session/CSRF interplay (same
 *     shape as `cancelAccountDeletion`, Story 1.12 §P22).
 *
 * All JSON field names stay snake_case (project-wide convention). Category
 * LABELS are the backend's French labels (`NotificationCategory.choices`)
 * — displayed as-is, never duplicated in `messages/fr.json`.
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type NotificationCategory =
  | "parcoursup_calendar"
  | "school_responses"
  | "new_schools"
  | "profile_completion"
  // Story 9.3 backend category — was missing from this union (drive-by fix
  // Story 10.2): the preferences GET returns it since the report queue ships.
  | "report_updates";

export interface NotificationPreference {
  category: NotificationCategory;
  /** Backend-provided French label — the display source of truth. */
  label: string;
  enabled: boolean;
}

export interface NotificationPreferencesResponse {
  /** Always all 4 categories (opt-out model: no row server-side = enabled). */
  preferences: NotificationPreference[];
}

export async function fetchNotificationPreferences(): Promise<NotificationPreferencesResponse> {
  return apiFetch<NotificationPreferencesResponse>("/api/v1/me/notification-preferences/");
}

export interface UpdatedNotificationPreference {
  category: NotificationCategory;
  enabled: boolean;
}

export async function updateNotificationPreference(
  category: NotificationCategory,
  enabled: boolean,
): Promise<UpdatedNotificationPreference> {
  return apiFetch<UpdatedNotificationPreference>("/api/v1/me/notification-preferences/", {
    method: "PUT",
    csrfToken: readCsrfCookie() ?? undefined,
    body: { category, enabled },
  });
}

export interface UnsubscribeResponse {
  category: NotificationCategory;
  /** French label of the category the token unsubscribed from. */
  label: string;
}

/**
 * One-click unsubscribe (public, logged-out). POST only — the mutation must
 * NEVER ride a GET: email-client prefetchers follow links, and a prefetcher
 * must never unsubscribe anyone (cf. the backend view's docstring).
 */
export async function unsubscribeByToken(token: string): Promise<UnsubscribeResponse> {
  return apiFetch<UnsubscribeResponse>("/api/v1/notifications/unsubscribe/", {
    method: "POST",
    body: { token },
  });
}

// --- Story 10.2 — Web Push -------------------------------------------------

/** `null` when the server has no VAPID config (204) — the toggle hides. */
export async function fetchVapidPublicKey(): Promise<string | null> {
  const res = await apiFetch<{ public_key: string } | null>(
    "/api/v1/notifications/push/vapid-public-key/",
  );
  return res?.public_key ?? null;
}

export interface PushSubscriptionPayload {
  endpoint: string;
  keys: { p256dh: string; auth: string };
}

export async function createPushSubscription(
  payload: PushSubscriptionPayload,
): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>("/api/v1/me/push-subscriptions/", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
    body: payload,
  });
}

export async function deletePushSubscription(endpoint: string): Promise<void> {
  await apiFetch<void>("/api/v1/me/push-subscriptions/", {
    method: "DELETE",
    csrfToken: readCsrfCookie() ?? undefined,
    body: { endpoint },
  });
}
