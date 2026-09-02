"use client";

/**
 * <StudentInvitationForm> — Story 6.5 §T7.2 client half.
 *
 * Submits `POST /students/invitation/{token}/accept/` with only the chosen
 * password (AC5 / §4.4 — no email field at all, the account already exists
 * from the CSV import). Success message differs for <15 vs >=15 accounts:
 * the backend returns the resulting `status`.
 */
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { acceptStudentInvitation } from "@/lib/api/establishments";

type Status = "idle" | "submitting" | "error" | "active" | "pending_parental_consent";

export function StudentInvitationForm({ token }: { token: string }) {
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatus("submitting");
    try {
      const result = await acceptStudentInvitation(token, password);
      setStatus(result.status === "active" ? "active" : "pending_parental_consent");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    }
  };

  if (status === "active") {
    return (
      <p className="text-body text-text">Ton compte est activé — connecte-toi pour continuer.</p>
    );
  }

  if (status === "pending_parental_consent") {
    return (
      <p className="text-body text-text">
        Ton mot de passe est enregistré. Il ne manque plus que la réponse d&apos;un parent ou tuteur
        pour activer ton compte.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="student-password">Choisis ton mot de passe</Label>
        <Input
          id="student-password"
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
        />
      </div>
      {status === "error" ? (
        <p role="alert" className="text-body-sm text-danger">
          {errorMessage}
        </p>
      ) : null}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Activation en cours…" : "Activer mon compte"}
      </Button>
    </form>
  );
}
