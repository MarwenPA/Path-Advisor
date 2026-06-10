"use client";

import { useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { confirmPasswordReset } from "@/lib/api/auth";

/*
 * ResetPasswordForm — Story 1.5 §AC6 §AC7.
 *
 * Receives `uid` + `token` from the URL (the reset link emailed by the
 * backend). Posts the new password to `/api/v1/auth/password/reset/confirm/`.
 *
 * Password rules are duplicated on the front for UX (length minimum) — the
 * authoritative validation runs server-side via Django's password validators.
 * A failed server validation surfaces as a 400 with the validators' error
 * messages, which we render directly.
 */

interface ResetPasswordFormProps {
  uid: string;
  token: string;
}

const COPY = {
  title: "Choisis un nouveau mot de passe",
  subtitle: "Saisis ton nouveau mot de passe deux fois pour confirmer.",
  newPasswordLabel: "Nouveau mot de passe",
  newPasswordHelp: "8 caractères minimum.",
  confirmPasswordLabel: "Confirme le nouveau mot de passe",
  submit: "Valider le nouveau mot de passe",
  submitting: "Mise à jour…",
  mismatch: "Les deux mots de passe ne correspondent pas.",
  tokenInvalid:
    "Ce lien est invalide ou expiré. Demande un nouveau lien depuis la page « Mot de passe oublié ».",
  rateLimited: "Trop de tentatives. Patiente quelques minutes avant de réessayer.",
  fallbackError: "Quelque chose n'a pas fonctionné. Réessaie dans un instant.",
  backToLogin: "Retour à la connexion",
};

export function ResetPasswordForm({ uid, token }: ResetPasswordFormProps) {
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;
    if (password1 !== password2) {
      setError(COPY.mismatch);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await confirmPasswordReset({
        uid,
        token,
        new_password1: password1,
        new_password2: password2,
      });
      // Success — full nav so any stale session is purged and the login
      // page renders fresh with a "?reset=success" hint banner.
      window.location.href = "/auth/login?reset=success";
    } catch (cause) {
      if (cause instanceof ApiError) {
        const type = cause.problem?.type ?? "";
        if (type.endsWith("/rate-limited")) {
          setError(COPY.rateLimited);
        } else if (cause.status === 400) {
          // dj-rest-auth surfaces token errors via {"token": [...]} and
          // password-validator errors via {"new_password2": [...]}. Both
          // are valid 400s; render the most informative string we can find.
          const problemErrors = cause.problem?.errors as Record<string, string[]> | undefined;
          if (problemErrors?.token) {
            setError(COPY.tokenInvalid);
          } else if (problemErrors) {
            // Concatenate password-validator messages so the user sees
            // "too common" / "too short" / etc. instead of a generic 400.
            const messages = Object.values(problemErrors).flat().join(" ");
            setError(messages || COPY.fallbackError);
          } else {
            setError(cause.problem?.detail ?? COPY.fallbackError);
          }
        } else {
          setError(cause.problem?.detail ?? COPY.fallbackError);
        }
      } else {
        setError(COPY.fallbackError);
      }
      setPassword2("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="flex w-full max-w-md flex-col gap-6 rounded-lg border border-border bg-bg p-6 shadow-sm">
      <header className="flex flex-col gap-1 text-center">
        <h1 className="text-h1 font-semibold text-text">{COPY.title}</h1>
        <p className="text-body-sm text-text-muted">{COPY.subtitle}</p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-2">
          <Label htmlFor="reset-password-1">{COPY.newPasswordLabel}</Label>
          <Input
            id="reset-password-1"
            name="new_password1"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password1}
            onChange={(e) => setPassword1(e.target.value)}
            disabled={submitting}
          />
          <p className="text-body-sm text-text-muted">{COPY.newPasswordHelp}</p>
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="reset-password-2">{COPY.confirmPasswordLabel}</Label>
          <Input
            id="reset-password-2"
            name="new_password2"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            disabled={submitting}
          />
        </div>

        {error && (
          <p role="alert" className="text-body-sm text-danger">
            {error}
          </p>
        )}

        <Button type="submit" disabled={submitting || !password1 || !password2}>
          {submitting ? COPY.submitting : COPY.submit}
        </Button>
      </form>

      <Link
        href="/auth/login"
        className="text-center text-body-sm text-brand underline-offset-2 hover:underline"
      >
        {COPY.backToLogin}
      </Link>
    </section>
  );
}
