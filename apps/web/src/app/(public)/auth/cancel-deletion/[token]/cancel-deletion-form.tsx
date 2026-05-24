"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { cancelAccountDeletion } from "@/lib/api/account-deletion";

interface CancelDeletionFormProps {
  token: string;
}

const LOGIN_REDIRECT = "/auth/login?cancellation=success";

export function CancelDeletionForm({ token }: CancelDeletionFormProps) {
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const isPendingRef = React.useRef(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isPendingRef.current) return;
    if (!password) return;
    isPendingRef.current = true;
    setSubmitting(true);
    setError(null);
    try {
      await cancelAccountDeletion(token, password);
      // Full nav to the login page so the next sign-in starts on a fresh
      // page (the user has no session at this point — there's nothing to
      // invalidate, but the redirect makes the success state visible).
      window.location.href = LOGIN_REDIRECT;
    } catch (cause) {
      const message =
        cause instanceof ApiError
          ? (cause.problem?.detail ?? cause.message)
          : "Une erreur a empêché l'annulation. Réessaie dans un instant.";
      setError(message);
      setPassword("");
    } finally {
      isPendingRef.current = false;
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3" noValidate>
      <label
        htmlFor="cancel-deletion-password"
        className="text-body-sm font-medium text-text"
      >
        Mot de passe actuel
      </label>
      <input
        id="cancel-deletion-password"
        name="password"
        type="password"
        autoComplete="current-password"
        required
        minLength={1}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={submitting}
        className="rounded-md border border-border bg-background px-3 py-2 text-body text-text focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30"
        aria-describedby={error ? "cancel-deletion-error" : undefined}
      />
      {error && (
        <p
          id="cancel-deletion-error"
          role="alert"
          className="text-body-sm text-danger"
        >
          {error}
        </p>
      )}
      <Button
        type="submit"
        disabled={submitting || password.length === 0}
        aria-disabled={submitting || password.length === 0}
      >
        {submitting ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
        ) : null}
        Annuler la suppression
      </Button>
      <p className="text-body-sm text-text-muted">
        Une fois annulée, tu pourras te reconnecter normalement.
      </p>
    </form>
  );
}
