"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { buildGdprDownloadUrl } from "@/lib/api/gdpr";
import type { GdprExportRequest } from "@/lib/api/gdpr";

import { GdprExportStatusBadge } from "./gdpr-export-status-badge";

interface GdprExportCardProps {
  export_: GdprExportRequest;
  onRetry?: () => void;
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function GdprExportCard({ export_, onRetry }: GdprExportCardProps) {
  const isActive = export_.status === "pending" || export_.status === "in_progress";

  return (
    <article
      id={export_.id}
      className="flex scroll-mt-24 flex-col gap-3 rounded-lg border border-border bg-bg p-4 target:ring-2 target:ring-brand"
    >
      <header className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <p className="text-sm text-text">Demande du {formatDateTime(export_.requested_at)}</p>
          <p className="text-xs text-text-muted">ID : {export_.id}</p>
        </div>
        <GdprExportStatusBadge status={export_.status} />
      </header>

      {isActive && (
        <p aria-live="polite" className="rounded bg-bg-2 px-3 py-2 text-sm text-text">
          Préparation de ton export en cours. Cela peut prendre jusqu&apos;à 30 minutes — tu
          recevras un email dès qu&apos;il sera prêt.
        </p>
      )}

      {export_.status === "ready" && (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-text-muted">
            Téléchargeable jusqu&apos;au {formatDateTime(export_.expires_at)} •{" "}
            {export_.download_count} / 10 téléchargements
          </p>
          <Button asChild>
            <Link
              href={buildGdprDownloadUrl(export_.id)}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Télécharger l'export du ${formatDateTime(export_.requested_at)}`}
            >
              Télécharger l&apos;archive
            </Link>
          </Button>
          <p className="text-xs text-text-subtle">
            L&apos;archive est protégée par un mot de passe. Tu l&apos;as reçu dans l&apos;email{" "}
            <em>&laquo;&nbsp;Mot de passe de ton export RGPD&nbsp;&raquo;</em>.
          </p>
        </div>
      )}

      {export_.status === "expired" && (
        <p className="text-sm text-text-muted">
          Ce lien a expiré. Lance un nouvel export pour récupérer tes données.
        </p>
      )}

      {export_.status === "failed" && (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-danger">
            L&apos;export n&apos;a pas pu aboutir
            {export_.error_code ? ` (code ${export_.error_code})` : ""}. Cette tentative ne consomme
            pas ton quota — tu peux retenter immédiatement.
          </p>
          {onRetry && (
            <Button variant="secondary" onClick={onRetry}>
              Retenter un export
            </Button>
          )}
        </div>
      )}
    </article>
  );
}
