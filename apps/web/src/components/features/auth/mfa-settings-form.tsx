"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { type CurrentUser } from "@/lib/api/auth";
import {
  mfaDisable,
  mfaEnrollStartFromSession,
  mfaRegenerateRecoveryCodes,
  storeMfaSession,
} from "@/lib/api/mfa";

/*
 * MfaSettingsForm — Story 1.6 §AC2, §AC6, §AC8.
 *
 * Reads the user prop (server-rendered) and renders one of three states:
 *
 * 1. Not enrolled, MFA required by role (staff) → big banner inviting
 *    enrollment via the login flow re-trigger.
 * 2. Not enrolled, B2C → "Activate MFA" call-to-action that bounces the
 *    user through the login flow (we don't have a standalone "enroll me
 *    now" endpoint — the user has to re-authenticate to get a fresh
 *    mfa_session).
 * 3. Enrolled → status panel + actions: regenerate recovery codes (always
 *    available), disable (B2C only).
 */

const COPY = {
  enrolledTitle: "Double authentification activée",
  enrolledDetails: (n: number) =>
    `Il te reste ${n} code${n > 1 ? "s" : ""} de récupération sur les 8 émis à ton enrôlement.`,
  staffNotEnrolledTitle: "MFA obligatoire — enrôle-toi maintenant",
  staffNotEnrolledBody:
    "Ton rôle staff impose la double authentification. Tu seras invité à l'enrôler à ta prochaine connexion. Si ce n'est pas déjà fait, reconnecte-toi pour démarrer le flow.",
  b2cNotEnrolledTitle: "Double authentification — non activée",
  b2cNotEnrolledBody:
    "Active la MFA pour ajouter une étape de vérification à tes connexions. À ta prochaine connexion, tu seras invité(e) à enrôler ton authenticator.",
  activateCta: "Activer la MFA",
  activateError: "Impossible de démarrer l'enrôlement. Réessaie dans un instant.",
  regenerateTitle: "Régénérer les codes de récupération",
  regenerateBody:
    "Les anciens codes seront immédiatement invalidés. Note bien les nouveaux : ils n'apparaîtront qu'une seule fois.",
  regenerateCta: "Régénérer mes 8 codes",
  disableTitle: "Désactiver la double authentification",
  disableBody:
    "Ton compte sera moins protégé. Re-confirme ton mot de passe + un code TOTP courant pour valider.",
  disableCta: "Désactiver la MFA",
  passwordLabel: "Mot de passe actuel",
  codeLabel: "Code TOTP courant",
  submitting: "Validation…",
  staffDisableForbidden:
    "Ton rôle staff impose la MFA. Tu ne peux pas la désactiver. Contacte le DPO si tu as perdu l'accès à ton authenticator.",
  wrongCredentials: "Mot de passe ou code TOTP incorrect.",
  fallbackError: "Quelque chose n'a pas fonctionné. Réessaie dans un instant.",
  freshCodesTitle: "Nouveaux codes — sauvegarde-les immédiatement",
  acknowledge: "J'ai sauvegardé mes nouveaux codes",
  done: "Terminé",
};

interface Props {
  user: CurrentUser;
}

type DialogMode = "idle" | "regenerate" | "disable";

export function MfaSettingsForm({ user }: Props) {
  const router = useRouter();
  const [dialog, setDialog] = useState<DialogMode>("idle");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [freshCodes, setFreshCodes] = useState<string[] | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);

  function closeDialog() {
    setDialog("idle");
    setPassword("");
    setCode("");
    setError(null);
    setFreshCodes(null);
    setAcknowledged(false);
  }

  async function handleReauthSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      // Code-review D4 — step-up is TOTP-only (no `method` field). Recovery
      // codes are NOT a valid second factor for destructive MFA operations.
      if (dialog === "regenerate") {
        const res = await mfaRegenerateRecoveryCodes({ password, code });
        setFreshCodes(res.recovery_codes);
      } else if (dialog === "disable") {
        await mfaDisable({ password, code });
        router.refresh();
        closeDialog();
      }
    } catch (cause) {
      if (cause instanceof ApiError) {
        const type = cause.problem?.type ?? "";
        if (type.endsWith("/mfa-disable-forbidden")) {
          setError(COPY.staffDisableForbidden);
        } else if (type.endsWith("/mfa-challenge-failed")) {
          setError(COPY.wrongCredentials);
        } else {
          setError(cause.problem?.detail ?? COPY.fallbackError);
        }
      } else {
        setError(COPY.fallbackError);
      }
    } finally {
      setSubmitting(false);
    }
  }

  // --- Fresh codes display after regenerate
  if (freshCodes) {
    return (
      <section className="space-y-4 rounded-lg border border-border bg-bg-2 p-6">
        <h2 className="text-h2 font-semibold">{COPY.freshCodesTitle}</h2>
        <div className="grid grid-cols-2 gap-2 rounded bg-white p-4 font-mono text-sm">
          {freshCodes.map((c) => (
            <code key={c} className="select-all">
              {c}
            </code>
          ))}
        </div>
        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => setAcknowledged(e.target.checked)}
            className="mt-1"
          />
          <span>{COPY.acknowledge}</span>
        </label>
        <Button
          type="button"
          className="w-full"
          disabled={!acknowledged}
          onClick={() => {
            router.refresh();
            closeDialog();
          }}
        >
          {COPY.done}
        </Button>
      </section>
    );
  }

  // --- Re-auth dialog (regenerate OR disable)
  if (dialog !== "idle") {
    const isDisable = dialog === "disable";
    return (
      <form
        onSubmit={handleReauthSubmit}
        className="space-y-4 rounded-lg border border-border bg-bg-2 p-6"
      >
        <h2 className="text-h2 font-semibold">
          {isDisable ? COPY.disableTitle : COPY.regenerateTitle}
        </h2>
        <p className="text-body text-text-muted">
          {isDisable ? COPY.disableBody : COPY.regenerateBody}
        </p>

        <div>
          <Label htmlFor="mfa-reauth-password">{COPY.passwordLabel}</Label>
          <Input
            id="mfa-reauth-password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="mfa-reauth-code">{COPY.codeLabel}</Label>
          <Input
            id="mfa-reauth-code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            required
            minLength={6}
            maxLength={6}
            pattern="[0-9]{6}"
          />
        </div>

        {error && (
          <p role="alert" className="text-text-error text-sm">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={closeDialog} disabled={submitting}>
            Annuler
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? COPY.submitting : isDisable ? COPY.disableCta : COPY.regenerateCta}
          </Button>
        </div>
      </form>
    );
  }

  // --- Default state — render based on enrollment + role
  if (user.mfa_enrolled) {
    return (
      <section className="space-y-4 rounded-lg border border-border bg-bg p-6">
        <header className="space-y-1">
          <h2 className="text-h2 font-semibold">{COPY.enrolledTitle}</h2>
          <p className="text-body text-text-muted">
            {COPY.enrolledDetails(user.mfa_recovery_codes_remaining)}
          </p>
        </header>

        <div className="flex flex-wrap gap-3">
          <Button type="button" onClick={() => setDialog("regenerate")}>
            {COPY.regenerateCta}
          </Button>
          {!user.mfa_required_by_role && (
            <Button type="button" variant="ghost" onClick={() => setDialog("disable")}>
              {COPY.disableCta}
            </Button>
          )}
        </div>
      </section>
    );
  }

  // Not enrolled — split staff (banner) vs B2C (CTA)
  if (user.mfa_required_by_role) {
    return (
      <section className="border-text-error space-y-2 rounded-lg border bg-red-50 p-6">
        <h2 className="text-text-error text-h2 font-semibold">{COPY.staffNotEnrolledTitle}</h2>
        <p className="text-body">{COPY.staffNotEnrolledBody}</p>
      </section>
    );
  }

  async function handleActivate() {
    setSubmitting(true);
    setError(null);
    try {
      // Code-review D3 — in-place enrollment instead of logout/re-login.
      // The new endpoint mints an `mfa_session` for the already-authenticated
      // user; we store it in sessionStorage and route to the same
      // `/auth/mfa/enroll` page the staff first-login flow uses.
      const res = await mfaEnrollStartFromSession();
      storeMfaSession(res.mfa_session);
      router.push("/auth/mfa/enroll");
    } catch {
      setError(COPY.activateError);
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-4 rounded-lg border border-border bg-bg p-6">
      <h2 className="text-h2 font-semibold">{COPY.b2cNotEnrolledTitle}</h2>
      <p className="text-body text-text-muted">{COPY.b2cNotEnrolledBody}</p>
      {error && (
        <p role="alert" className="text-text-error text-sm">
          {error}
        </p>
      )}
      <Button type="button" onClick={handleActivate} disabled={submitting}>
        {submitting ? COPY.submitting : COPY.activateCta}
      </Button>
    </section>
  );
}
