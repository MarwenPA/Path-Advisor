"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { SideFlow } from "@/components/ui/side-flow";
import { useCurrentUser } from "@/hooks/use-current-user";
import { resendParentalConsentEmail } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

/**
 * Parental-consent SideFlow instance — Story 10.6, replaces the Story 1.4
 * `LimitedModeBanner`.
 *
 * Three states keyed on `parental_consent_state` (server-derived — the old
 * banner keyed on `status` alone and offered "resend" even when the consent
 * was already granted or expired, where the endpoint 404s):
 *
 *  - `pending`  → parent hasn't decided: reassuring copy + "Relancer mon
 *    parent" (the /resend/ endpoint is rate-limited 1/h → 429 handled).
 *  - `granted`  → parent said yes but the student's email is unverified:
 *    different copy, NO resend CTA (nothing to resend to the parent).
 *  - `expired` / `none` → the 60-day window closed: point to support.
 *
 * Resolution (AC): while pending, the user is polled every 30 s (ADD-8 — no
 * WebSocket in MVP); when the parent validates AND the email is verified the
 * status flips to `active`, the banner disappears and SideFlow shows the
 * "compte entièrement actif" toast.
 */
const POLL_MS = 30_000;

type ResendStatus = "idle" | "loading" | "sent" | "rate-limited" | "error";

export function ParentalConsentSideFlow() {
  const t = useTranslations("sideFlow.parentalConsent");
  const router = useRouter();
  const [resendStatus, setResendStatus] = useState<ResendStatus>("idle");

  const { data: user } = useCurrentUser({
    pollWhile: (u) => (u?.status === "pending_parental_consent" ? POLL_MS : false),
  });

  const open = user?.status === "pending_parental_consent" && !user.is_fully_active;
  const consentState = user?.parental_consent_state ?? "none";

  const onResend = async () => {
    setResendStatus("loading");
    try {
      await resendParentalConsentEmail();
      setResendStatus("sent");
    } catch (error) {
      if (error instanceof ApiError && error.problem?.status === 429) {
        setResendStatus("rate-limited");
        return;
      }
      setResendStatus("error");
    }
  };

  const message =
    consentState === "granted"
      ? t("grantedMessage")
      : consentState === "pending"
        ? t("pendingMessage")
        : t("expiredMessage");

  const cta =
    consentState === "pending"
      ? {
          label: resendStatus === "loading" ? t("resending") : t("resend"),
          onClick: () => void onResend(),
          disabled: resendStatus === "loading" || resendStatus === "sent",
        }
      : consentState === "granted"
        ? undefined
        : { label: t("goToSupport"), onClick: () => router.push("/support") };

  const feedback =
    consentState === "pending" ? (
      <>
        {resendStatus === "sent" && <span className="text-success">{t("resendSuccess")}</span>}
        {resendStatus === "rate-limited" && (
          <span className="text-text-muted">{t("rateLimited")}</span>
        )}
        {resendStatus === "error" && <span className="text-danger">{t("resendFailed")}</span>}
      </>
    ) : undefined;

  return (
    <SideFlow
      open={Boolean(open)}
      message={message}
      cta={cta}
      feedback={feedback}
      resolvedMessage={t("resolvedToast")}
    />
  );
}
