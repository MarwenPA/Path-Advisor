/**
 * Browser-side Web Push plumbing — Story 10.2.
 *
 * The subscription lives in the BROWSER (push service endpoint + keys); the
 * API only mirrors it (`/me/push-subscriptions/`) so the worker can send.
 * Everything here degrades silently: unsupported browser, missing VAPID
 * config (API answers 204) or denied permission each map to a distinct
 * status the settings toggle turns into calm copy — never an error screen
 * (NFR-R4: emails keep flowing regardless).
 */

import {
  createPushSubscription,
  deletePushSubscription,
  fetchVapidPublicKey,
} from "@/lib/api/notifications";

export type EnablePushResult = "subscribed" | "denied" | "unsupported" | "unconfigured";

export function isPushSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

/** The `applicationServerKey` wants raw bytes, the API serves base64url.
 * Explicit `ArrayBuffer` backing: CI's stricter TS rejects
 * `Uint8Array<ArrayBufferLike>` where `BufferSource` is expected. */
function urlBase64ToUint8Array(base64url: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64url.length % 4)) % 4);
  const base64 = (base64url + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const output = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i += 1) output[i] = raw.charCodeAt(i);
  return output;
}

export async function getPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushSupported()) return null;
  const registration = await navigator.serviceWorker.getRegistration("/");
  if (!registration) return null;
  return registration.pushManager.getSubscription();
}

export async function enablePush(): Promise<EnablePushResult> {
  if (!isPushSupported()) return "unsupported";

  const publicKey = await fetchVapidPublicKey();
  if (!publicKey) return "unconfigured";

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return "denied";

  const registration = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey),
  });
  const json = subscription.toJSON();
  await createPushSubscription({
    endpoint: json.endpoint ?? subscription.endpoint,
    keys: { p256dh: json.keys?.p256dh ?? "", auth: json.keys?.auth ?? "" },
  });
  return "subscribed";
}

/**
 * AC2: revokes BOTH sides — the API row first (no push may be queued after
 * this resolves), then the browser subscription itself.
 */
export async function disablePush(): Promise<void> {
  const subscription = await getPushSubscription();
  if (!subscription) return;
  await deletePushSubscription(subscription.endpoint);
  await subscription.unsubscribe();
}
