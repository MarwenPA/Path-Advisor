"use client";

/**
 * <SendOutreachButton> — Story 5.4 §AC1/AC2/AC3.
 *
 * Rendered on `/schools/[slug]` for a premium student. Two-step Sheet:
 * 1. Pick "métier visé" (among the student's own recommendations) +
 *    optional motivation.
 * 2. Confirmation screen listing exactly what will be shared (name,
 *    métier visé, motivation if any — NOT the student's other
 *    recommendations, per the epic's own privacy framing).
 *
 * `parcours` is resolved server-side — no picker here (§2 scope decision).
 * On confirm: creates the request, redirects to `/mes-envois`.
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { createOutreachRequest } from "@/lib/api/outreach";
import type { ScoredProfession } from "@/lib/api/recommendations";

type Step = "form" | "confirm";
type Status = "idle" | "submitting" | "error";

export interface SendOutreachButtonProps {
  schoolSlug: string;
  schoolName: string;
  professions: ScoredProfession[];
}

export function SendOutreachButton({
  schoolSlug,
  schoolName,
  professions,
}: SendOutreachButtonProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>("form");
  const [professionId, setProfessionId] = useState<string>(professions[0]?.id ?? "");
  const [motivation, setMotivation] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const selectedProfession = professions.find((p) => p.id === professionId);
  const wordCount = motivation.trim() === "" ? 0 : motivation.trim().split(/\s+/).length;

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) {
      setStep("form");
      setStatus("idle");
      setErrorMessage(null);
    }
  }

  async function handleConfirm() {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      await createOutreachRequest(schoolSlug, {
        profession_id: professionId,
        motivation_text: motivation,
      });
      router.push("/mes-envois");
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
    <>
      <Button onClick={() => setOpen(true)} disabled={professions.length === 0}>
        Envoyer mon profil à cette école
      </Button>

      <Sheet open={open} onOpenChange={handleOpenChange}>
        <SheetContent side="bottom">
          {step === "form" ? (
            <>
              <SheetHeader>
                <SheetTitle>Envoyer mon profil à {schoolName}</SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-4 py-4">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="outreach-profession">Métier visé</Label>
                  <Select value={professionId} onValueChange={setProfessionId}>
                    <SelectTrigger id="outreach-profession">
                      <SelectValue placeholder="Choisis un métier" />
                    </SelectTrigger>
                    <SelectContent>
                      {professions.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="outreach-motivation">Motivation (facultatif, 200-500 mots)</Label>
                  <Textarea
                    id="outreach-motivation"
                    value={motivation}
                    onChange={(event) => setMotivation(event.target.value)}
                    rows={5}
                    maxLength={4000}
                    placeholder="Quelques angles possibles : ce qui t'attire dans ce métier, un projet ou une expérience qui t'y a mené, ce que tu cherches dans cette école en particulier…"
                  />
                  <p className="text-caption text-text-subtle">{wordCount} mots</p>
                </div>
              </div>
              <SheetFooter>
                <Button onClick={() => setStep("confirm")} disabled={!professionId}>
                  Continuer
                </Button>
              </SheetFooter>
            </>
          ) : (
            <>
              <SheetHeader>
                <SheetTitle>Vérifie avant d&apos;envoyer</SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-3 py-4 text-body-sm text-text">
                <p>{schoolName} verra :</p>
                <ul className="list-disc pl-5">
                  <li>Ton profil scolaire synthétique</li>
                  <li>Le métier visé : {selectedProfession?.name}</li>
                  {motivation ? <li>Ta motivation</li> : null}
                </ul>
                <p className="text-text-muted">
                  L&apos;école ne verra ni tes autres métiers recommandés, ni les autres écoles que
                  tu cibles.
                </p>
                {motivation ? (
                  <p className="text-text-muted">
                    Ta motivation passe d&apos;abord par une relecture (sous 24h ouvrées) avant
                    d&apos;être envoyée à l&apos;école.
                  </p>
                ) : null}
                {status === "error" ? (
                  <p role="alert" className="text-danger">
                    {errorMessage}
                  </p>
                ) : null}
              </div>
              <SheetFooter className="gap-2">
                <Button
                  variant="outline"
                  onClick={() => setStep("form")}
                  disabled={status === "submitting"}
                >
                  Retour
                </Button>
                <Button onClick={handleConfirm} disabled={status === "submitting"}>
                  {status === "submitting" ? "Envoi en cours…" : "Confirmer l'envoi"}
                </Button>
              </SheetFooter>
            </>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
