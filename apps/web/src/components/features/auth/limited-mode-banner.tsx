"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { CurrentUser, fetchCurrentUser, resendParentalConsentEmail } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

const COPY = {
  message:
    "Tu es en mode découverte : tes parents doivent valider ton inscription pour débloquer toutes les fonctionnalités.",
  resend: "Renvoyer l'email",
  resending: "Envoi en cours…",
  resendSuccess: "Email renvoyé à ton parent.",
  rateLimited: "Trop tôt — réessaie dans une heure.",
  resendFailed: "Impossible de renvoyer l'email pour l'instant.",
};

/**
 * Layout-level banner that appears for users in `pending_parental_consent` (Story 1.4
 * §AC7). Renders nothing when:
 *  - the user is fully active (banner is the wrong message)
 *  - the fetch fails (we don't want to flash a misleading error in authenticated layouts)
 *
 * No `useCurrentUser` extracted to a hook for MVP — only one consumer today.
 */
export function LimitedModeBanner() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [resendStatus, setResendStatus] = useState<
    "idle" | "loading" | "sent" | "error" | "rate-limited"
  >("idle");

  useEffect(() => {
    let cancelled = false;
    fetchCurrentUser()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        // Anonymous or session expired — banner stays hidden.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Story 1.4 review §P9: this banner's copy talks about parental validation —
  // only render it for users actually in `pending_parental_consent`. An adult
  // ≥ 15 ans whose email is unverified would otherwise see a misleading message.
  // Future stories may add their own banners for `email_unverified` / `suspended`.
  if (!user || user.is_fully_active || user.status !== "pending_parental_consent") return null;

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

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-bg-2 px-4 py-3 text-body-sm text-text"
    >
      <p className="min-w-0 flex-1">{COPY.message}</p>
      <div className="flex items-center gap-3">
        {resendStatus === "sent" && <span className="text-success">{COPY.resendSuccess}</span>}
        {resendStatus === "rate-limited" && (
          <span className="text-text-muted">{COPY.rateLimited}</span>
        )}
        {resendStatus === "error" && <span className="text-danger">{COPY.resendFailed}</span>}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onResend}
          disabled={resendStatus === "loading" || resendStatus === "sent"}
        >
          {resendStatus === "loading" ? COPY.resending : COPY.resend}
        </Button>
      </div>
    </div>
  );
}
