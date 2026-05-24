import type { GdprExportStatus } from "@/lib/api/gdpr";

import { cn } from "@/lib/utils";

const LABEL: Record<GdprExportStatus, string> = {
  pending: "En attente",
  in_progress: "En cours",
  ready: "Prêt",
  expired: "Expiré",
  failed: "Échec",
};

// The design system only ships single-tone tokens (`warning`, `success`,
// `danger`) plus muted greys. We use a `/15` alpha modifier on the fill so the
// label keeps high contrast for RGAA AA (≥ 4.5:1) — the colour is also never
// the only signal: the text label is rendered alongside.
const TONE: Record<GdprExportStatus, string> = {
  pending: "bg-warning/15 text-warning",
  in_progress: "bg-warning/15 text-warning",
  ready: "bg-success/15 text-success",
  expired: "bg-bg-2 text-text-muted",
  failed: "bg-danger/15 text-danger",
};

export function GdprExportStatusBadge({ status }: { status: GdprExportStatus }) {
  return (
    <span
      role="status"
      aria-label={`Statut de l'export : ${LABEL[status]}`}
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        TONE[status],
      )}
    >
      {LABEL[status]}
    </span>
  );
}
