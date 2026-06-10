"use client";

/**
 * <RevokeAccessButton> — Story 1.10 §AC6, §T6 + review patches P8 P16.
 *
 * Client Component island inside the otherwise server-rendered
 * <TierAccessCard>. Opens a <ConsentDialog> (Story 1.14) on click, sends
 * POST /api/v1/profile/access-list/<id>/revoke/ on confirm, refreshes the
 * page so the entry disappears from the server-rendered list.
 *
 * Review P8 — success path renders an inline "Accès révoqué." confirmation
 * (aria-live, SR-friendly) BEFORE router.refresh swaps the card out.
 * Review P16 — re-opening the dialog after a 5xx error resets the status so
 * the user gets a fresh attempt instead of seeing stale state.
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ConsentDialog, type ConsentMeta } from "@/components/ui/consent-dialog";
import { ApiError } from "@/lib/api/client";
import { revokeAccessListEntry, type AccessListEntry } from "@/lib/api/access-list";
import { ACCESS_LIST_COPY, REVOKE_DIALOG_COPY, type DataAreaKey } from "@/lib/i18n/fr/access-list";

type Status = "idle" | "submitting" | "success" | "not-found" | "error";

export function RevokeAccessButton({ entry }: { entry: AccessListEntry }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status>("idle");

  const dialogCopy = REVOKE_DIALOG_COPY[entry.tier_type];
  const dataMentionedLabels = entry.visible_data.map(
    (area) => ACCESS_LIST_COPY.dataAreaLabels[area as DataAreaKey] ?? area,
  );

  // Review P16 — when the dialog re-opens after a previous error / success,
  // reset state so the user sees a clean attempt.
  const handleOpenChange = (next: boolean) => {
    if (next && (status === "error" || status === "success")) {
      setStatus("idle");
    }
    setOpen(next);
  };

  // Review P8 — fade the success confirmation after a few seconds so it
  // doesn't linger after `router.refresh` swaps the card out. Cleanup on
  // unmount or status change.
  useEffect(() => {
    if (status !== "success") return;
    const timer = setTimeout(() => setStatus("idle"), 4_000);
    return () => clearTimeout(timer);
  }, [status]);

  const handleAccept = async (meta: ConsentMeta) => {
    setStatus("submitting");
    try {
      await revokeAccessListEntry(entry.id, meta.contentHash);
      setStatus("success");
      setOpen(false);
      router.refresh();
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) {
        setStatus("not-found");
        setOpen(false);
        // Optimistic refresh so the (stale) entry disappears anyway.
        router.refresh();
        return;
      }
      setStatus("error");
    }
  };

  return (
    <div className="flex flex-col items-end gap-2">
      <Button variant="ghost" onClick={() => handleOpenChange(true)} disabled={status === "submitting"}>
        {ACCESS_LIST_COPY.revokeButtonLabel}
      </Button>

      {status === "error" ? (
        <p className="text-text-error text-sm" role="alert">
          {dialogCopy.errorMessage}
        </p>
      ) : null}

      {/* Review P8 — inline success confirmation. `aria-live="polite"` so
          screen-reader users hear it. Auto-fades via useEffect above. */}
      {status === "success" ? (
        <p className="text-sm text-text-muted" role="status" aria-live="polite">
          {ACCESS_LIST_COPY.revokeSuccessInline}
        </p>
      ) : null}

      <ConsentDialog
        open={open}
        onOpenChange={handleOpenChange}
        title={dialogCopy.title}
        description={dialogCopy.description}
        dataMentioned={dataMentionedLabels}
        duration={dialogCopy.duration}
        beneficiary={entry.display_name}
        acceptLabel={dialogCopy.acceptLabel}
        refuseLabel={dialogCopy.refuseLabel}
        isAcceptDestructive
        isSubmitting={status === "submitting"}
        onAccept={handleAccept}
      />
    </div>
  );
}
