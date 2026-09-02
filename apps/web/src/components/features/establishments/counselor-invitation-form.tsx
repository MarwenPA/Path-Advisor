"use client";

/**
 * <CounselorInvitationForm> — Story 6.5 §T7.1 client half.
 *
 * Submits `POST /auth/counselor-invitation/{token}/accept/` with only the
 * chosen password (AC4 / §4.4 — the account email is locked to the
 * invitation, never editable here). No auto-login: on success the user is
 * redirected to `/auth/login` — `requires_mfa=True` means the normal login +
 * MFA-enrollment flow must run next (AC4 third clause).
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { acceptCounselorInvitation } from "@/lib/api/establishments";

type Status = "idle" | "submitting" | "error" | "done";

export function CounselorInvitationForm({ token }: { token: string }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatus("submitting");
    try {
      await acceptCounselorInvitation(token, password);
      setStatus("done");
      router.push("/auth/login");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    }
  };

  if (status === "done") {
    return <p className="text-body text-text">Compte créé — connecte-toi pour continuer.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="counselor-password">Mot de passe</Label>
        <Input
          id="counselor-password"
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
        {status === "submitting" ? "Création en cours…" : "Créer mon compte"}
      </Button>
    </form>
  );
}
