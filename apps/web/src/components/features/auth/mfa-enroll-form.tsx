"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { getPostLoginPath } from "@/lib/auth/post-login-redirect";
import {
  clearMfaSession,
  mfaEnrollConfirm,
  mfaEnrollStart,
  readMfaSession,
  type MfaEnrollStartResponse,
} from "@/lib/api/mfa";

/*
 * MfaEnrollForm — Story 1.6 §AC1, §AC2.
 *
 * 3-step flow:
 *   1. Mount → call POST /api/v1/auth/mfa/enroll/start/ with the mfa_session
 *      from sessionStorage → render the QR code + base32 secret fallback.
 *   2. User scans QR with their authenticator app, types the first 6-digit
 *      TOTP code → call POST /api/v1/auth/mfa/enroll/confirm/.
 *   3. On success: show the 8 recovery codes with a mandatory
 *      "J'ai sauvegardé mes codes" checkbox before routing to dashboard.
 */

const COPY = {
  title: "Configure ta double authentification",
  subtitle:
    "Scanne ce QR code avec ton application authenticator (Google Authenticator, Authy, 1Password, etc.), puis valide avec le code à 6 chiffres.",
  manualSecretLabel: "Saisir manuellement",
  manualSecretHelp: "Si ton authenticator ne peut pas scanner, copie ce secret :",
  codeLabel: "Code à 6 chiffres",
  codeHelp: "Le code généré par ton authenticator change toutes les 30 secondes.",
  submit: "Confirmer l'enrôlement",
  submitting: "Vérification…",
  recoveryTitle: "Tes 8 codes de récupération",
  recoveryHelp:
    "Note ou imprime ces codes. Chacun est à usage unique et te permettra de te connecter si tu perds ton authenticator. Tu ne les reverras jamais.",
  saveAcknowledge: "J'ai sauvegardé mes codes de récupération",
  copyAll: "Copier tous",
  continue: "Continuer vers mon espace",
  invalidCode: "Code incorrect. Vérifie ton authenticator et réessaie.",
  expiredSession:
    "Ta session de configuration a expiré. Reconnecte-toi pour relancer l'enrôlement.",
  fallbackError:
    "Quelque chose n'a pas fonctionné. Vérifie ta connexion et réessaie dans un instant.",
  missingSession:
    "Aucune session MFA active. Connecte-toi à nouveau pour relancer l'enrôlement.",
};

export function MfaEnrollForm() {
  const router = useRouter();
  const [startData, setStartData] = useState<MfaEnrollStartResponse | null>(null);
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [postLoginPath, setPostLoginPath] = useState<string>("/");

  // Read mfa_session once on first client render (SSR-safe). Lazy init
  // keeps the value stable and lets us derive the initial error state
  // synchronously — avoiding `react-hooks/set-state-in-effect`.
  const [initialToken] = useState<string | null>(() =>
    typeof window === "undefined" ? null : readMfaSession(),
  );
  const [error, setError] = useState<string | null>(() =>
    typeof window === "undefined" || initialToken ? null : COPY.missingSession,
  );

  const startedRef = useRef(false);

  // Bootstrap: call /enroll/start/ once on mount when a token is present.
  useEffect(() => {
    if (startedRef.current || !initialToken) return;
    startedRef.current = true;

    mfaEnrollStart(initialToken)
      .then(setStartData)
      .catch((cause) => {
        if (cause instanceof ApiError) {
          const type = cause.problem?.type ?? "";
          if (type.endsWith("/mfa-session-expired")) {
            setError(COPY.expiredSession);
            return;
          }
        }
        setError(COPY.fallbackError);
      });
  }, [initialToken]);

  async function handleConfirm(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;
    const token = readMfaSession();
    if (!token) {
      setError(COPY.missingSession);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await mfaEnrollConfirm(token, code.trim());
      setRecoveryCodes(res.recovery_codes);
      setPostLoginPath(getPostLoginPath(res.user.role, res.user.status));
      // The session cookie is now posted — clear the ephemeral mfa_session.
      clearMfaSession();
    } catch (cause) {
      if (cause instanceof ApiError) {
        const type = cause.problem?.type ?? "";
        if (type.endsWith("/mfa-challenge-failed")) {
          setError(COPY.invalidCode);
        } else if (
          type.endsWith("/mfa-session-expired") ||
          type.endsWith("/mfa-session-invalid")
        ) {
          setError(COPY.expiredSession);
        } else {
          setError(cause.problem?.detail ?? COPY.fallbackError);
        }
      } else {
        setError(COPY.fallbackError);
      }
      setCode("");
    } finally {
      setSubmitting(false);
    }
  }

  function handleContinue() {
    router.refresh();
    router.replace(postLoginPath);
  }

  function handleCopyAll() {
    if (!recoveryCodes) return;
    navigator.clipboard.writeText(recoveryCodes.join("\n")).catch(() => undefined);
  }

  // --- Step 3: recovery codes display
  if (recoveryCodes) {
    return (
      <section className="w-full max-w-md space-y-6">
        <header className="space-y-2">
          <h1 className="text-h2">{COPY.recoveryTitle}</h1>
          <p className="text-text-muted">{COPY.recoveryHelp}</p>
        </header>

        <div className="grid grid-cols-2 gap-2 rounded-lg border border-border bg-bg-2 p-4 font-mono text-sm">
          {recoveryCodes.map((c) => (
            <code key={c} className="select-all">
              {c}
            </code>
          ))}
        </div>

        <div className="flex justify-end">
          <Button type="button" variant="ghost" onClick={handleCopyAll}>
            {COPY.copyAll}
          </Button>
        </div>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => setAcknowledged(e.target.checked)}
            className="mt-1"
          />
          <span>{COPY.saveAcknowledge}</span>
        </label>

        <Button
          type="button"
          className="w-full"
          disabled={!acknowledged}
          onClick={handleContinue}
        >
          {COPY.continue}
        </Button>
      </section>
    );
  }

  // --- Step 1: error / loading
  if (error && !startData) {
    return (
      <section className="w-full max-w-md space-y-4">
        <h1 className="text-h2">{COPY.title}</h1>
        <p className="text-text-error">{error}</p>
      </section>
    );
  }

  if (!startData) {
    return (
      <section className="w-full max-w-md space-y-4">
        <h1 className="text-h2">{COPY.title}</h1>
        <p className="text-text-muted">Préparation de ton QR code…</p>
      </section>
    );
  }

  // --- Step 2: QR code + code input
  // Extract the base32 secret from otpauth_url for the manual-entry fallback.
  const secretMatch = startData.otpauth_url.match(/[?&]secret=([^&]+)/);
  const secret = secretMatch?.[1] ?? "";

  return (
    <section className="w-full max-w-md space-y-6">
      <header className="space-y-2">
        <h1 className="text-h2">{COPY.title}</h1>
        <p className="text-text-muted">{COPY.subtitle}</p>
      </header>

      <div
        className="flex justify-center rounded-lg border border-border bg-white p-4"
        dangerouslySetInnerHTML={{ __html: startData.qr_svg }}
      />

      <details className="rounded-lg border border-border bg-bg-2 p-3">
        <summary className="cursor-pointer text-sm font-medium">
          {COPY.manualSecretLabel}
        </summary>
        <div className="mt-2 space-y-2">
          <p className="text-sm text-text-muted">{COPY.manualSecretHelp}</p>
          <code className="block select-all break-all rounded bg-white p-2 font-mono text-xs">
            {secret}
          </code>
        </div>
      </details>

      <form onSubmit={handleConfirm} className="space-y-4">
        <div>
          <Label htmlFor="mfa-code">{COPY.codeLabel}</Label>
          <Input
            id="mfa-code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            required
            minLength={6}
            maxLength={6}
            pattern="[0-9]{6}"
            autoFocus
          />
          <p className="mt-1 text-xs text-text-muted">{COPY.codeHelp}</p>
        </div>

        {error && (
          <p role="alert" className="text-sm text-text-error">
            {error}
          </p>
        )}

        <Button
          type="submit"
          className="w-full"
          disabled={submitting || code.length !== 6}
        >
          {submitting ? COPY.submitting : COPY.submit}
        </Button>
      </form>
    </section>
  );
}
