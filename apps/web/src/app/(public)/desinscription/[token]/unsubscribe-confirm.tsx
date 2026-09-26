"use client";

/**
 * One-click confirm flow for /desinscription/[token] — Story 8.2 §AC3.
 *
 * State machine: confirm → pending → done | invalid, with a retryable
 * transient-error branch. The POST happens EXCLUSIVELY in the button's
 * click handler — no effect, no render-time call — so a prefetched or
 * merely-opened page never unsubscribes anyone (`page.test.tsx` pins this).
 *
 * Works logged-out: `unsubscribeByToken` hits the public AllowAny endpoint
 * (no CSRF — the backend declares `authentication_classes = []`).
 */
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { unsubscribeByToken } from "@/lib/api/notifications";

interface UnsubscribeConfirmProps {
  token: string;
}

type FlowState =
  | { step: "confirm"; retryError: boolean }
  | { step: "pending" }
  | { step: "done"; label: string }
  | { step: "invalid" };

export function UnsubscribeConfirm({ token }: UnsubscribeConfirmProps) {
  const t = useTranslations("notifications.unsubscribe");
  const [state, setState] = useState<FlowState>({ step: "confirm", retryError: false });

  const handleConfirm = async () => {
    setState({ step: "pending" });
    try {
      const { label } = await unsubscribeByToken(token);
      setState({ step: "done", label });
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 400) {
        // Invalid/tampered token — terminal error state.
        setState({ step: "invalid" });
      } else {
        // Transient failure (network, throttle, 5xx) — let the user retry.
        setState({ step: "confirm", retryError: true });
      }
    }
  };

  if (state.step === "done") {
    return (
      <section
        role="status"
        className="flex flex-col gap-3 rounded-lg border border-border bg-bg p-6"
      >
        <h2 className="text-h2 font-semibold text-text">{t("successTitle")}</h2>
        <p className="text-body text-text-muted">{t("successBody", { label: state.label })}</p>
        <p className="text-body-sm text-text-muted">
          {t("manageBeforeLink")}
          <Link href="/parametres/notifications" className="text-brand underline">
            {t("manageLink")}
          </Link>
          {t("manageAfterLink")}
        </p>
      </section>
    );
  }

  if (state.step === "invalid") {
    return (
      <section
        role="alert"
        className="flex flex-col gap-3 rounded-lg border border-border bg-bg p-6"
      >
        <h2 className="text-h2 font-semibold text-text">{t("invalidTitle")}</h2>
        <p className="text-body text-text-muted">{t("invalidBody")}</p>
      </section>
    );
  }

  const pending = state.step === "pending";
  return (
    <div className="flex flex-col gap-4">
      <p className="text-body text-text-muted">{t("explanation")}</p>
      {state.step === "confirm" && state.retryError && (
        <p role="alert" className="text-body-sm text-danger">
          {t("retryError")}
        </p>
      )}
      <Button
        type="button"
        onClick={() => void handleConfirm()}
        disabled={pending}
        aria-disabled={pending}
      >
        {pending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden /> : null}
        {pending ? t("pendingCta") : t("confirmCta")}
      </Button>
    </div>
  );
}
