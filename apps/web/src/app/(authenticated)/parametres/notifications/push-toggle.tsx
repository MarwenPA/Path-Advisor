"use client";

/**
 * Push opt-in toggle — Story 10.2 (AC opt-in + AC dégradation gracieuse).
 *
 * L'état "activé" vient du NAVIGATEUR (`pushManager.getSubscription()`),
 * pas de l'API : c'est l'abonnement de CET appareil qu'on pilote. Deux
 * absences rendent le bloc invisible, jamais une erreur : navigateur sans
 * Push API, ou VAPID non configuré côté serveur (204). Une permission
 * refusée ramène le toggle à off avec une phrase calme (le navigateur
 * bloque les re-prompts de toute façon).
 *
 * RGAA : même patron que les toggles de catégories (label réel, état en
 * texte visible, pas de couleur seule). Toggle optimiste comme la liste
 * (P2-8a : jamais `disabled` pendant l'appel — ça éjecte le focus).
 */
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { Switch } from "@/components/ui/switch";
import { fetchVapidPublicKey } from "@/lib/api/notifications";
import { disablePush, enablePush, getPushSubscription, isPushSupported } from "@/lib/push";

interface ToggleState {
  visible: boolean;
  enabled: boolean;
  pending: boolean;
  notice: "none" | "denied" | "error";
}

const HIDDEN: ToggleState = { visible: false, enabled: false, pending: false, notice: "none" };

export function PushToggle() {
  const t = useTranslations("notifications.settings.push");
  const [state, setState] = useState<ToggleState>(HIDDEN);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (!isPushSupported()) return;
        const key = await fetchVapidPublicKey();
        if (!key) return;
        const subscription = await getPushSubscription();
        if (!cancelled) {
          setState({
            visible: true,
            enabled: subscription !== null,
            pending: false,
            notice: "none",
          });
        }
      } catch {
        // API indisponible — le bloc reste caché, les emails continuent.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!state.visible) return null;

  const handleToggle = async (next: boolean) => {
    if (state.pending) return;
    // Optimiste : le switch suit le geste, puis se réconcilie avec le réel.
    setState({ visible: true, enabled: next, pending: true, notice: "none" });
    try {
      if (next) {
        const result = await enablePush();
        setState({
          visible: true,
          enabled: result === "subscribed",
          pending: false,
          notice: result === "denied" ? "denied" : "none",
        });
      } else {
        await disablePush();
        setState({ visible: true, enabled: false, pending: false, notice: "none" });
      }
    } catch {
      setState({ visible: true, enabled: !next, pending: false, notice: "error" });
    }
  };

  return (
    <section
      aria-labelledby="push-toggle-title"
      className="flex flex-col gap-1 rounded-lg border border-border bg-bg p-4"
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-1">
          <label
            id="push-toggle-title"
            htmlFor="push-toggle"
            className="text-body font-medium text-text"
          >
            {t("label")}
          </label>
          <p className="text-body-sm text-text-muted">{t("description")}</p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span aria-hidden className="text-body-sm text-text-muted">
            {state.pending ? t("statePending") : state.enabled ? t("stateOn") : t("stateOff")}
          </span>
          <Switch
            id="push-toggle"
            checked={state.enabled}
            aria-busy={state.pending}
            onChange={(event) => void handleToggle(event.target.checked)}
          />
        </div>
      </div>
      {state.notice === "denied" && (
        <p role="status" className="text-body-sm text-text-muted">
          {t("denied")}
        </p>
      )}
      {state.notice === "error" && (
        <p role="alert" className="text-body-sm text-danger">
          {t("error")}
        </p>
      )}
    </section>
  );
}
