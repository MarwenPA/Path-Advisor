"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { getPostLoginPath } from "@/lib/auth/post-login-redirect";
import {
  clearMfaSession,
  mfaChallenge,
  readMfaSession,
  type MfaChallengeMethod,
} from "@/lib/api/mfa";

/*
 * MfaChallengeForm — Story 1.6 §AC3, §AC4.
 *
 * Two modes: TOTP (default, 6-digit) and recovery (xxxx-xxxx-xxxx).
 * On success the backend posts the session cookie + returns the user.
 */

const COPY = {
  title: "Vérifie ton identité",
  subtitle: "Ouvre ton authenticator et saisis le code à 6 chiffres.",
  totpLabel: "Code à 6 chiffres",
  recoveryLabel: "Code de récupération",
  recoveryHelp: "Format : xxxx-xxxx-xxxx",
  switchToRecovery: "Utiliser un code de récupération",
  switchToTotp: "Revenir au code TOTP",
  submit: "Valider",
  submitting: "Vérification…",
  invalidCode: "Code incorrect. Vérifie ton code et réessaie.",
  expiredSession:
    "Ta session de vérification a expiré. Reconnecte-toi pour relancer la double authentification.",
  fallbackError:
    "Quelque chose n'a pas fonctionné. Vérifie ta connexion et réessaie dans un instant.",
  missingSession:
    "Aucune session MFA active. Reconnecte-toi pour relancer la double authentification.",
  backToLogin: "Retour à la connexion",
};

export function MfaChallengeForm() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [method, setMethod] = useState<MfaChallengeMethod>("totp");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittingRef = useRef(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submittingRef.current) return;
    const token = readMfaSession();
    if (!token) {
      setError(COPY.missingSession);
      return;
    }
    submittingRef.current = true;
    setSubmitting(true);
    setError(null);

    try {
      const trimmed = method === "totp" ? code.replace(/\D/g, "") : code.trim();
      const res = await mfaChallenge(token, trimmed, method);
      clearMfaSession();
      const path = getPostLoginPath(res.user.role, res.user.status);
      router.refresh();
      router.replace(path);
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
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  function switchMethod() {
    setError(null);
    setCode("");
    setMethod(method === "totp" ? "recovery" : "totp");
  }

  const isTotp = method === "totp";
  const isComplete = isTotp ? code.length === 6 : code.length >= 14;

  return (
    <section className="w-full max-w-md space-y-6">
      <header className="space-y-2">
        <h1 className="text-h2">{COPY.title}</h1>
        <p className="text-text-muted">{COPY.subtitle}</p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="mfa-challenge-code">
            {isTotp ? COPY.totpLabel : COPY.recoveryLabel}
          </Label>
          <Input
            id="mfa-challenge-code"
            type="text"
            inputMode={isTotp ? "numeric" : "text"}
            autoComplete="one-time-code"
            value={code}
            onChange={(e) => {
              const v = isTotp ? e.target.value.replace(/\D/g, "").slice(0, 6) : e.target.value;
              setCode(v);
            }}
            required
            minLength={isTotp ? 6 : 14}
            maxLength={isTotp ? 6 : 20}
            pattern={isTotp ? "[0-9]{6}" : undefined}
            autoFocus
          />
          {!isTotp && <p className="mt-1 text-xs text-text-muted">{COPY.recoveryHelp}</p>}
        </div>

        {error && (
          <p role="alert" className="text-sm text-text-error">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={submitting || !isComplete}>
          {submitting ? COPY.submitting : COPY.submit}
        </Button>
      </form>

      <button
        type="button"
        className="text-sm text-text-muted underline"
        onClick={switchMethod}
      >
        {isTotp ? COPY.switchToRecovery : COPY.switchToTotp}
      </button>

      <p className="text-xs text-text-muted">
        <a href="/auth/login" className="underline">
          {COPY.backToLogin}
        </a>
      </p>
    </section>
  );
}
