"use client";

/**
 * <ResubmitMotivationForm> — Story 5.5.
 *
 * Shown on `/mes-envois` for a `rejected` request: displays the admin's
 * `rejection_reason`, lets the student rewrite the motivation (200-500
 * words, same rule as the initial submission), and resubmits it — which
 * puts the request back into `pending_moderation`.
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { resubmitOutreachRequest } from "@/lib/api/outreach";

export interface ResubmitMotivationFormProps {
  outreachId: string;
  rejectionReason: string;
}

export function ResubmitMotivationForm({
  outreachId,
  rejectionReason,
}: ResubmitMotivationFormProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [motivation, setMotivation] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit() {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      await resubmitOutreachRequest(outreachId, motivation);
      router.refresh();
      setOpen(false);
      setMotivation("");
      setStatus("idle");
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "Une erreur est survenue. Réessaie dans quelques instants.",
      );
    }
  }

  return (
    <div className="mt-2 rounded-md bg-danger/5 p-3">
      <p className="text-body-sm text-text">
        <strong>Motif du refus :</strong> {rejectionReason}
      </p>
      {open ? (
        <div className="mt-2 flex flex-col gap-2">
          <Textarea
            value={motivation}
            onChange={(event) => setMotivation(event.target.value)}
            rows={5}
            maxLength={4000}
            placeholder="Réécris ta motivation (200-500 mots)…"
          />
          <p className="text-caption text-text-subtle">{motivation.length} caractères</p>
          {status === "error" ? (
            <p role="alert" className="text-danger">
              {errorMessage}
            </p>
          ) : null}
          <div className="flex gap-2">
            <Button onClick={handleSubmit} disabled={status === "submitting"}>
              {status === "submitting" ? "Envoi en cours…" : "Soumettre à nouveau"}
            </Button>
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={status === "submitting"}
            >
              Annuler
            </Button>
          </div>
        </div>
      ) : (
        <Button variant="outline" className="mt-2" onClick={() => setOpen(true)}>
          Réécrire ma motivation
        </Button>
      )}
    </div>
  );
}
