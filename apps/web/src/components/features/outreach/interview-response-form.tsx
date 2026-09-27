"use client";

/**
 * <InterviewResponseForm> — Story 5.7, upgraded Story 10.4.
 *
 * Shown on `/mes-envois` for a request whose school response is
 * `interview_requested` and still undecided: lets the student accept one
 * of the proposed slots, or (single round, §2 scope decision — no
 * back-and-forth negotiation loop) suggest one free-text alternative
 * instead.
 *
 * Story 10.4 (AC1 "mini-calendrier") : les créneaux sont groupés par jour
 * avec l'heure en bouton, fuseau **Europe/Paris explicite** — le rendu
 * serveur de /mes-envois et le navigateur de l'élève doivent afficher la
 * même heure (incohérence 5.7 consignée).
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { acceptInterviewSlot, proposeInterviewAlternative } from "@/lib/api/outreach";

export interface InterviewResponseFormProps {
  outreachId: string;
  proposedSlots: string[];
}

/** Mini-calendrier : créneaux groupés par jour (Europe/Paris). */
function groupSlotsByDay(slots: string[]) {
  const days = new Map<string, { iso: string; hour: string }[]>();
  for (const iso of slots) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) continue;
    const day = date.toLocaleDateString("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      timeZone: "Europe/Paris",
    });
    const hour = date.toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Europe/Paris",
    });
    const bucket = days.get(day) ?? [];
    bucket.push({ iso, hour });
    days.set(day, bucket);
  }
  return Array.from(days.entries(), ([day, daySlots]) => ({ day, slots: daySlots }));
}

export function InterviewResponseForm({ outreachId, proposedSlots }: InterviewResponseFormProps) {
  const router = useRouter();
  const [mode, setMode] = useState<"choose" | "alternative">("choose");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function accept(slot: string) {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      await acceptInterviewSlot(outreachId, slot);
      router.refresh();
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    }
  }

  async function submitAlternative() {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      await proposeInterviewAlternative(outreachId, note);
      router.refresh();
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    }
  }

  return (
    <div className="mt-2 rounded-md bg-primary/5 p-3">
      <p className="text-body-sm text-text">L&apos;école te propose un entretien :</p>
      {status === "error" ? (
        <p role="alert" className="mt-1 text-danger">
          {errorMessage}
        </p>
      ) : null}
      {mode === "choose" ? (
        <div className="mt-2 flex flex-col gap-2">
          {groupSlotsByDay(proposedSlots).map(({ day, slots }) => (
            <div
              key={day}
              className="flex flex-col gap-2 rounded-md border border-border bg-bg p-3"
            >
              <span className="text-body-sm font-medium capitalize text-text">{day}</span>
              <div className="flex flex-wrap gap-2">
                {slots.map(({ iso, hour }) => (
                  <Button
                    key={iso}
                    variant="outline"
                    size="sm"
                    onClick={() => accept(iso)}
                    disabled={status === "submitting"}
                  >
                    {hour}
                  </Button>
                ))}
              </div>
            </div>
          ))}
          <Button
            variant="ghost"
            onClick={() => setMode("alternative")}
            disabled={status === "submitting"}
          >
            Aucun de ces créneaux ne me convient
          </Button>
        </div>
      ) : (
        <div className="mt-2 flex flex-col gap-2">
          <Textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            placeholder="Explique tes disponibilités…"
          />
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setMode("choose")}
              disabled={status === "submitting"}
            >
              Retour
            </Button>
            <Button onClick={submitAlternative} disabled={status === "submitting" || !note.trim()}>
              Envoyer
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
