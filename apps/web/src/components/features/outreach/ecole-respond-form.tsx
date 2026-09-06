"use client";

/**
 * <EcoleRespondForm> — Story 5.7 (+ Story 5.12 keyboard shortcuts).
 *
 * Rendered on `/ecole/outreach/[id]` for a `pending` request. 3 explicit
 * actions (épic AC): "Profil intéressant" (primary), "Profil non aligné"
 * (secondary, with a respectful-tone reminder before confirming — inline
 * rather than a full generic `ConsentDialog`, same §2 scope decision
 * pattern as Story 5.4's send flow), "Demande d'entretien" (tertiary,
 * proposes 2-3 slots). Optional comment (≤200 words) on every action.
 *
 * Story 5.12 AC — keyboard shortcuts on the "choose" step: `i` (intéressant,
 * submits directly), `n` (non aligné, opens the confirm step), `e`
 * (entretien, opens the slots step). Ignored while typing in the comment
 * textarea (so a student's name containing "i" doesn't misfire) and while
 * a submission is in flight.
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { respondToOutreachRequest, type EcoleResponseAction } from "@/lib/api/ecole-outreach";

type Step = "choose" | "confirm-not-aligned" | "interview-slots";
type Status = "idle" | "submitting" | "error";

export interface EcoleRespondFormProps {
  outreachId: string;
}

const NOT_ALIGNED_TEMPLATE =
  "Ton profil est intéressant mais ne correspond pas à nos critères cette année. Continue à explorer !";

export function EcoleRespondForm({ outreachId }: EcoleRespondFormProps) {
  const router = useRouter();
  const [step, setStep] = useState<Step>("choose");
  const [comment, setComment] = useState("");
  const [slots, setSlots] = useState<string[]>(["", "", ""]);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const commentWordCount = comment.trim() === "" ? 0 : comment.trim().split(/\s+/).length;

  async function submit(action: EcoleResponseAction, proposedSlots?: string[]) {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      await respondToOutreachRequest(outreachId, {
        action,
        comment,
        proposed_slots: proposedSlots,
      });
      router.refresh();
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "Une erreur est survenue. Réessaie dans quelques instants.",
      );
    }
  }

  const filledSlots = slots.map((s) => s.trim()).filter(Boolean);

  useEffect(() => {
    if (step !== "choose") return;
    function onKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target?.tagName === "TEXTAREA" || target?.tagName === "INPUT") return;
      if (status === "submitting") return;
      if (e.key === "i") submit("interested");
      else if (e.key === "n") setStep("confirm-not-aligned");
      else if (e.key === "e") setStep("interview-slots");
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, status]);

  if (step === "confirm-not-aligned") {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="mb-2 text-body-sm text-text">
          Le message que reçoit l&apos;élève doit rester respectueux et constructif.
        </p>
        <Textarea
          value={comment || NOT_ALIGNED_TEMPLATE}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          maxLength={2000}
        />
        {status === "error" ? (
          <p role="alert" className="mt-2 text-danger">
            {errorMessage}
          </p>
        ) : null}
        <div className="mt-3 flex gap-2">
          <Button
            variant="outline"
            onClick={() => setStep("choose")}
            disabled={status === "submitting"}
          >
            Retour
          </Button>
          <Button onClick={() => submit("not_aligned")} disabled={status === "submitting"}>
            {status === "submitting" ? "Envoi…" : "Confirmer"}
          </Button>
        </div>
      </div>
    );
  }

  if (step === "interview-slots") {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="mb-2 text-body-sm text-text">Propose 2 à 3 créneaux (visio externe) :</p>
        {slots.map((slot, i) => (
          <input
            key={i}
            type="datetime-local"
            value={slot}
            onChange={(e) => {
              const next = [...slots];
              next[i] = e.target.value;
              setSlots(next);
            }}
            className="mb-2 block w-full rounded border border-border px-3 py-2 text-body-sm"
          />
        ))}
        {status === "error" ? (
          <p role="alert" className="mt-2 text-danger">
            {errorMessage}
          </p>
        ) : null}
        <div className="mt-3 flex gap-2">
          <Button
            variant="outline"
            onClick={() => setStep("choose")}
            disabled={status === "submitting"}
          >
            Retour
          </Button>
          <Button
            onClick={() =>
              submit(
                "interview_requested",
                filledSlots.map((s) => new Date(s).toISOString()),
              )
            }
            disabled={status === "submitting" || filledSlots.length < 2}
          >
            {status === "submitting" ? "Envoi…" : "Proposer ces créneaux"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="mb-2 text-body-sm text-text">Commentaire pour l&apos;élève (facultatif) :</p>
      <Textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        maxLength={2000}
        placeholder="Max 200 mots…"
      />
      <p className="mb-3 text-caption text-text-subtle">{commentWordCount} / 200 mots</p>
      {status === "error" ? (
        <p role="alert" className="mb-2 text-danger">
          {errorMessage}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => submit("interested")} disabled={status === "submitting"}>
          Profil intéressant — candidature encouragée
        </Button>
        <Button
          variant="outline"
          onClick={() => setStep("confirm-not-aligned")}
          disabled={status === "submitting"}
        >
          Profil non aligné
        </Button>
        <Button
          variant="ghost"
          onClick={() => setStep("interview-slots")}
          disabled={status === "submitting"}
        >
          📅 Demande d&apos;entretien
        </Button>
      </div>
    </div>
  );
}
