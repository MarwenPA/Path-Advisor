"use client";

/**
 * <CancelSubscriptionButton> — Story 5.3 §T8/AC3.
 *
 * Same pattern as `RevokeAccessButton` (Story 1.10): opens a `ConsentDialog`
 * on click, POSTs the cancellation on confirm, refreshes the page so the
 * settings page re-renders with `cancel_at_period_end: true`. Cancellation is
 * scheduled at period end, NOT immediate — the user keeps premium until then.
 */
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ConsentDialog } from "@/components/ui/consent-dialog";
import { cancelSubscription } from "@/lib/api/billing";
import { BILLING_COPY } from "@/lib/i18n/fr/billing";

type Status = "idle" | "submitting" | "success" | "error";

export function CancelSubscriptionButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const COPY = BILLING_COPY.settings;
  const dialogCopy = COPY.cancelDialog;

  const handleOpenChange = (next: boolean) => {
    if (next && status === "error") setStatus("idle");
    setOpen(next);
  };

  const handleAccept = async () => {
    setStatus("submitting");
    try {
      await cancelSubscription();
      setStatus("success");
      setOpen(false);
      router.refresh();
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        variant="ghost"
        onClick={() => handleOpenChange(true)}
        disabled={status === "submitting"}
      >
        {COPY.cancelCta}
      </Button>

      {status === "error" ? (
        <p className="text-text-error text-sm" role="alert">
          {dialogCopy.errorMessage}
        </p>
      ) : null}

      <ConsentDialog
        open={open}
        onOpenChange={handleOpenChange}
        title={dialogCopy.title}
        description={dialogCopy.description}
        dataMentioned={[]}
        duration={dialogCopy.duration}
        beneficiary={dialogCopy.beneficiary}
        acceptLabel={dialogCopy.acceptLabel}
        refuseLabel={dialogCopy.refuseLabel}
        isAcceptDestructive
        isSubmitting={status === "submitting"}
        onAccept={handleAccept}
      />
    </div>
  );
}
