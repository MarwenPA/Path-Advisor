/**
 * Story 10.2 — Web Push service worker.
 *
 * Volontairement minimal : PAS de cache offline, pas de PWA — uniquement la
 * réception des push (payload chiffré aes128gcm, décodé par le navigateur)
 * et le clic. Le payload est construit côté API (`notifications/push.py`)
 * avec une copie sobre, sûre pour un écran verrouillé.
 *
 * Servi depuis public/ à la racine → scope "/" par défaut.
 */

self.addEventListener("push", (event) => {
  if (!event.data) return;
  let payload;
  try {
    payload = event.data.json();
  } catch {
    return; // Payload inattendu — on n'affiche jamais du contenu non structuré.
  }
  const title = typeof payload.title === "string" && payload.title ? payload.title : "Path-Advisor";
  event.waitUntil(
    self.registration.showNotification(title, {
      body: typeof payload.body === "string" ? payload.body : "",
      icon: "/logo.svg",
      data: { url: typeof payload.url === "string" ? payload.url : "/" },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    (async () => {
      const windows = await clients.matchAll({ type: "window", includeUncontrolled: true });
      for (const client of windows) {
        if ("focus" in client) {
          await client.focus();
          if ("navigate" in client) await client.navigate(url);
          return;
        }
      }
      await clients.openWindow(url);
    })(),
  );
});
