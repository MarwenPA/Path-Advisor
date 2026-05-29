"use client";

import { useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { requestPasswordReset } from "@/lib/api/auth";

/*
 * ForgotPasswordForm — Story 1.5 §AC5 §AC7.
 *
 * Single-input email form. The backend always responds 200 with an
 * identical body whether the email is known or not — we mirror that
 * anti-enumeration shape on the front-end by always showing the same
 * success message ("Si cet email existe…").
 */

const COPY = {
  title: "Mot de passe oublié ?",
  subtitle:
    "Saisis ton email — on t'enverra un lien pour réinitialiser ton mot de passe.",
  emailLabel: "Adresse email",
  submit: "Envoyer le lien",
  submitting: "Envoi…",
  successTitle: "Vérifie ta boîte mail",
  successBody:
    "Si cet email existe, un lien de réinitialisation t'a été envoyé. Le lien est valable 1 heure.",
  fallbackError:
    "Quelque chose n'a pas fonctionné. Réessaie dans quelques instants.",
  rateLimited:
    "Trop de demandes. Patiente quelques minutes avant de réessayer.",
  backToLogin: "Retour à la connexion",
};

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await requestPasswordReset(email);
      setDone(true);
    } catch (cause) {
      if (cause instanceof ApiError && cause.problem?.type?.endsWith("/rate-limited")) {
        setError(COPY.rateLimited);
      } else {
        setError(COPY.fallbackError);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <section className="flex w-full max-w-md flex-col gap-4 rounded-lg border border-border bg-bg p-6 shadow-sm">
        <h1 className="text-h1 font-semibold text-text">{COPY.successTitle}</h1>
        <p className="text-body text-text-muted">{COPY.successBody}</p>
        <Link
          href="/auth/login"
          className="text-body-sm text-brand underline-offset-2 hover:underline"
        >
          {COPY.backToLogin}
        </Link>
      </section>
    );
  }

  return (
    <section className="flex w-full max-w-md flex-col gap-6 rounded-lg border border-border bg-bg p-6 shadow-sm">
      <header className="flex flex-col gap-1 text-center">
        <h1 className="text-h1 font-semibold text-text">{COPY.title}</h1>
        <p className="text-body-sm text-text-muted">{COPY.subtitle}</p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-2">
          <Label htmlFor="forgot-email">{COPY.emailLabel}</Label>
          <Input
            id="forgot-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={submitting}
          />
        </div>

        {error && (
          <p role="alert" className="text-body-sm text-danger">
            {error}
          </p>
        )}

        <Button type="submit" disabled={submitting || !email}>
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
