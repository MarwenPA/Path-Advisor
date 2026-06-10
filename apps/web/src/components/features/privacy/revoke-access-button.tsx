"use client";

/**
 * <RevokeAccessButton> — Story 1.10 §AC6, §T6.
 *
 * Client Component island inside the otherwise server-rendered
 * <TierAccessCard>. Opens a <ConsentDialog> (Story 1.14) on click, sends
 * POST /api/v1/profile/access-list/<id>/revoke/ on confirm, refreshes the
 * page so the entry disappears from the server-rendered list.
 *
 * Tier-specific dialog copy lives in `ACCESS_LIST_COPY.revokeDialog` so the
 * UX writer touches one file. The Story 1.14 ConsentDialog computes the
 * content hash from the displayed props ; the backend stores it as audit
 * forensic proof (NOT a gate — see backend `revoker.py`).
 */
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ConsentDialog, type ConsentMeta } from "@/components/ui/consent-dialog";
import { ApiError } from "@/lib/api/client";
import { revokeAccessListEntry, type AccessListEntry } from "@/lib/api/access-list";
import {
  ACCESS_LIST_COPY,
  REVOKE_DIALOG_COPY,
  type DataAreaKey,
} from "@/lib/i18n/fr/access-list";

type Status = "idle" | "submitting" | "success" | "not-found" | "error";

export function RevokeAccessButton({ entry }: { entry: AccessListEntry }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status>("idle");

  const dialogCopy = REVOKE_DIALOG_COPY[entry.tier_type];
  const dataMentionedLabels = entry.visible_data.map(
    (area) =>
      ACCESS_LIST_COPY.dataAreaLabels[area as DataAreaKey] ?? area,
  );

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
      <Button
        variant="ghost"
        onClick={() => setOpen(true)}
        disabled={status === "submitting"}
      >
        {ACCESS_LIST_COPY.revokeButtonLabel}
      </Button>

      {status === "error" ? (
        <p className="text-sm text-text-error" role="alert">
          {dialogCopy.errorMessage}
        </p>
      ) : null}

      <ConsentDialog
        open={open}
        onOpenChange={setOpen}
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
