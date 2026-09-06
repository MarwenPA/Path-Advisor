"use client";

/**
 * <ViewAccessHistoryButton> — Story 6.11. Client Component island (same
 * pattern as `<RevokeAccessButton>`) opening `<AccessHistoryModal>`.
 */
import { useState } from "react";

import { AccessHistoryModal } from "@/components/features/privacy/access-history-modal";
import { ACCESS_LIST_COPY } from "@/lib/i18n/fr/access-list";

export function ViewAccessHistoryButton({ entryId }: { entryId: string }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-card"
      >
        {ACCESS_LIST_COPY.viewHistoryButtonLabel}
      </button>
      {open && <AccessHistoryModal entryId={entryId} onClose={() => setOpen(false)} />}
    </>
  );
}
