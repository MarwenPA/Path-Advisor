"use client";

/**
 * <InviteParentDialog> — Story 6.1 §T7.2.
 *
 * Two-step flow: a plain form (email + relationship + custom message)
 * followed by the shared `<ConsentDialog>` (Story 1.14, NOT re-created here)
 * that gates the actual `POST /parent-invitations/` call behind an explicit
 * "J'ai compris" acknowledgement (AC1).
 */
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ConsentDialog } from "@/components/ui/consent-dialog";
import { ApiError } from "@/lib/api/client";
import { createParentInvitation, type ParentRelationship } from "@/lib/api/family";
import { FAMILY_COPY } from "@/lib/i18n/fr/family";

type Step = "form" | "consent";
type Status = "idle" | "submitting" | "error" | "already-pending";

export function InviteParentDialog({ onInvited }: { onInvited?: (maskedEmail: string) => void }) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>("form");
  const [status, setStatus] = useState<Status>("idle");
  const [parentEmail, setParentEmail] = useState("");
  const [relationship, setRelationship] = useState<ParentRelationship | "">("");
  const [customMessage, setCustomMessage] = useState("");

  const resetAndClose = () => {
    setOpen(false);
    setStep("form");
    setStatus("idle");
    setParentEmail("");
    setRelationship("");
    setCustomMessage("");
  };

  const handleFormSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!parentEmail) return;
    setStep("consent");
  };

  const handleAccept = async () => {
    setStatus("submitting");
    try {
      const invitation = await createParentInvitation({
        parent_email: parentEmail,
        relationship: relationship || undefined,
        custom_message: customMessage || undefined,
      });
      onInvited?.(invitation.parent_email);
      resetAndClose();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setStatus("already-pending");
        return;
      }
      setStatus("error");
    }
  };

  return (
    <Dialog
      open={open && step === "form"}
      onOpenChange={(next) => {
        if (!next) resetAndClose();
        else setOpen(true);
      }}
    >
      <DialogTrigger asChild>
        <Button onClick={() => setOpen(true)}>{FAMILY_COPY.inviteButtonLabel}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{FAMILY_COPY.inviteButtonLabel}</DialogTitle>
          <DialogDescription>{FAMILY_COPY.pageDescription}</DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={handleFormSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="parent-email">{FAMILY_COPY.form.emailLabel}</Label>
            <Input
              id="parent-email"
              type="email"
              required
              placeholder={FAMILY_COPY.form.emailPlaceholder}
              value={parentEmail}
              onChange={(event) => setParentEmail(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="parent-relationship">{FAMILY_COPY.form.relationshipLabel}</Label>
            <Select
              value={relationship}
              onValueChange={(value) => setRelationship(value as ParentRelationship)}
            >
              <SelectTrigger id="parent-relationship">
                <SelectValue placeholder={FAMILY_COPY.form.relationshipLabel} />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(FAMILY_COPY.form.relationshipOptions).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="parent-message">{FAMILY_COPY.form.messageLabel}</Label>
            <Input
              id="parent-message"
              maxLength={FAMILY_COPY.form.messageMaxLength}
              placeholder={FAMILY_COPY.form.messagePlaceholder}
              value={customMessage}
              onChange={(event) => setCustomMessage(event.target.value)}
            />
          </div>
          {status === "already-pending" ? (
            <p role="alert" className="text-text-error text-sm">
              {FAMILY_COPY.errors.alreadyPending}
            </p>
          ) : null}
          {status === "error" ? (
            <p role="alert" className="text-text-error text-sm">
              {FAMILY_COPY.errors.generic}
            </p>
          ) : null}
          <Button type="submit" disabled={!parentEmail}>
            {FAMILY_COPY.form.submitLabel}
          </Button>
        </form>
      </DialogContent>

      <ConsentDialog
        open={open && step === "consent"}
        onOpenChange={(next) => {
          if (!next) setStep("form");
        }}
        title={FAMILY_COPY.consentDialog.title}
        description={FAMILY_COPY.consentDialog.description}
        dataMentioned={[...FAMILY_COPY.consentDialog.dataMentioned]}
        duration={FAMILY_COPY.consentDialog.duration}
        beneficiary={FAMILY_COPY.consentDialog.beneficiary}
        acceptLabel={FAMILY_COPY.consentDialog.acceptLabel}
        refuseLabel={FAMILY_COPY.consentDialog.refuseLabel}
        isSubmitting={status === "submitting"}
        onAccept={handleAccept}
        onRefuse={() => setStep("form")}
      />
    </Dialog>
  );
}

export default InviteParentDialog;
