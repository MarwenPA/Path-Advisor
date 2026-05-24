"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ConsentDialog, type ConsentMeta } from "@/components/ui/consent-dialog";
import { ApiError } from "@/lib/api/client";
import { decideParentalConsent, type ParentalConsentStatus } from "@/lib/api/auth";

type DialogVariant = "grant" | "refuse" | null;

const GRANT_CONSENT_PROPS = {
  title: "Autoriser l'inscription de votre enfant",
  description:
    "En cliquant sur « J'autorise », vous confirmez avoir lu les informations ci-dessus et autoriser votre enfant à utiliser Path-Advisor.",
  dataMentioned: [
    "Profil scolaire (bulletins, passions, intérêts)",
    "Métiers explorés",
    "Parcours sauvegardés",
  ],
  duration: "Jusqu'aux 18 ans de l'enfant (révocable à tout moment)",
  acceptLabel: "J'autorise",
  refuseLabel: "Annuler",
  isAcceptDestructive: false as const,
};

const REFUSE_CONSENT_PROPS = {
  title: "Refuser l'inscription",
  description:
    "En cliquant sur « Je refuse », vous bloquez l'inscription de votre enfant. Cette action est irréversible pour cette demande.",
  dataMentioned: [
    "Aucune donnée scolaire ne sera collectée",
    "Le compte sera mis en pause immédiatement",
  ],
  duration: "Action immédiate, irréversible pour cette demande",
  acceptLabel: "Je refuse",
  refuseLabel: "Annuler",
  isAcceptDestructive: true as const,
};

export function ParentalConsentFlow({
  token,
  initial,
}: {
  token: string;
  initial: ParentalConsentStatus;
}) {
  const [status, setStatus] = useState<ParentalConsentStatus["status"]>(initial.status);
  const [openDialog, setOpenDialog] = useState<DialogVariant>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const beneficiary = `Votre enfant (${initial.student_email_masked})`;

  const submitDecision = async (decision: "granted" | "refused", meta: ConsentMeta) => {
    setSubmitting(true);
    setError(null);
    try {
      await decideParentalConsent(token, {
        decision,
        content_hash: meta.contentHash,
        accepted_at: meta.acceptedAt,
      });
      setStatus(decision);
      setOpenDialog(null);
    } catch (err) {
      if (err instanceof ApiError && err.problem?.status === 409) {
        setStatus("expired");
        setError(
          "Cette demande a déjà reçu une décision ou a expiré. Vous pouvez fermer cette page.",
        );
        return;
      }
      setError(
        err instanceof ApiError
          ? (err.problem?.detail ?? "Erreur lors de l'enregistrement de votre décision.")
          : "Erreur lors de l'enregistrement de votre décision.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (status === "granted") {
    return (
      <section
        aria-labelledby="grant-success-title"
        className="flex flex-col gap-3 rounded-md border border-success/40 bg-success/10 p-6"
      >
        <h2 id="grant-success-title" className="text-h2 font-semibold text-text md:text-h2-desktop">
          Merci, votre enfant a maintenant accès à Path-Advisor.
        </h2>
        <p className="text-body text-text-muted">
          Vous pouvez fermer cette page. Vous recevrez plus d&apos;informations par email si
          nécessaire.
        </p>
      </section>
    );
  }

  if (status === "refused") {
    return (
      <section
        aria-labelledby="refuse-success-title"
        className="flex flex-col gap-3 rounded-md border border-border bg-bg-2 p-6"
      >
        <h2
          id="refuse-success-title"
          className="text-h2 font-semibold text-text md:text-h2-desktop"
        >
          Votre refus a été enregistré.
        </h2>
        <p className="text-body text-text-muted">
          Aucun email ne sera envoyé à votre enfant. Vous pouvez fermer cette page.
        </p>
      </section>
    );
  }

  if (status === "expired") {
    return (
      <section
        aria-labelledby="expired-title"
        className="flex flex-col gap-3 rounded-md border border-border bg-bg-2 p-6"
      >
        <h2 id="expired-title" className="text-h2 font-semibold text-text md:text-h2-desktop">
          Lien expiré ou déjà utilisé
        </h2>
        <p className="text-body text-text-muted">
          {error ??
            "Cette demande n'est plus active. Vous pouvez fermer cette page sans rien faire."}
        </p>
      </section>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div
          role="alert"
          className="rounded-md border border-danger/40 bg-danger/10 p-4 text-body-sm text-danger"
        >
          {error}
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          type="button"
          onClick={() => setOpenDialog("grant")}
          disabled={submitting}
          className="w-full sm:w-auto"
        >
          Autoriser
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => setOpenDialog("refuse")}
          disabled={submitting}
          className="w-full sm:w-auto"
        >
          Refuser
        </Button>
      </div>

      <ConsentDialog
        open={openDialog === "grant"}
        onOpenChange={(open) => !open && setOpenDialog(null)}
        beneficiary={beneficiary}
        isSubmitting={submitting}
        onAccept={(meta) => submitDecision("granted", meta)}
        onRefuse={() => setOpenDialog(null)}
        {...GRANT_CONSENT_PROPS}
      />

      <ConsentDialog
        open={openDialog === "refuse"}
        onOpenChange={(open) => !open && setOpenDialog(null)}
        beneficiary={beneficiary}
        isSubmitting={submitting}
        onAccept={(meta) => submitDecision("refused", meta)}
        onRefuse={() => setOpenDialog(null)}
        {...REFUSE_CONSENT_PROPS}
      />
    </div>
  );
}
