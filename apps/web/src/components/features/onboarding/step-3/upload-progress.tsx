"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { UploadFile } from "./onboarding-step3-machine";

type Props = {
  files: UploadFile[];
  onRetry?: (fileId: string) => void;
  onModifySelection?: () => void;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadProgress({ files, onRetry, onModifySelection }: Props) {
  const totalBytes = files.reduce((s, f) => s + f.file.size, 0);
  const uploadedBytes = files.reduce((s, f) => s + (f.progress / 100) * f.file.size, 0);
  const doneCount = files.filter((f) => f.status === "done").length;
  const failedCount = files.filter((f) => f.status === "failed").length;

  const prefersReducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  return (
    <section aria-label="Progression de l'envoi" className="flex flex-col gap-4 w-full">
      <h2 className="text-[var(--text-h2)] font-semibold text-[var(--color-text)]">
        On envoie tes bulletins…
      </h2>

      <p className="text-sm text-[var(--color-text-muted)]" aria-live="polite">
        Fichier {doneCount} sur {files.length} — {formatBytes(uploadedBytes)} / {formatBytes(totalBytes)}
      </p>

      <ul className="flex flex-col gap-3 list-none p-0" role="list">
        {files.map((f) => {
          const progressValue = f.status === "done" ? 100 : f.status === "failed" ? 0 : f.progress;
          return (
            <li key={f.id} className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-[var(--color-text)] truncate max-w-[200px]">
                  {f.file.name}
                </span>
                {f.status === "done" && (
                  <CheckCircle2
                    className="size-4 text-[var(--color-brand)] shrink-0"
                    aria-label="Envoyé"
                  />
                )}
                {f.status === "failed" && (
                  <span className="flex items-center gap-1 text-[var(--color-warning)] text-xs shrink-0">
                    <AlertTriangle className="size-3" aria-hidden />
                    Pas réussi
                  </span>
                )}
                {(f.status === "uploading" || f.status === "pending") && (
                  <span className="text-xs text-[var(--color-text-subtle)]">
                    {f.status === "uploading" ? `${f.progress} %` : "En attente…"}
                  </span>
                )}
              </div>

              <Progress
                value={progressValue}
                className={cn(
                  "h-1",
                  f.status === "failed" && "opacity-40",
                  prefersReducedMotion && "[&>*]:transition-none"
                )}
                aria-valuenow={progressValue}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Progression ${f.file.name}`}
              />

              {f.status === "failed" && (
                <div className="flex gap-2 mt-1">
                  {onRetry && (
                    <button
                      type="button"
                      onClick={() => onRetry(f.id)}
                      className="text-xs text-[var(--color-brand)] underline underline-offset-2 focus-visible:outline-[var(--color-brand)]"
                    >
                      Réessayer ce fichier
                    </button>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {failedCount > 0 && (
        <p role="alert" className="text-sm text-[var(--color-warning)]">
          {failedCount > 1
            ? `${failedCount} fichiers n'ont pas pu être envoyés.`
            : "1 fichier n'a pas pu être envoyé."}
          {onModifySelection && (
            <button
              type="button"
              onClick={onModifySelection}
              className="ml-2 underline underline-offset-2 text-[var(--color-brand)]"
            >
              Modifier la sélection
            </button>
          )}
        </p>
      )}
    </section>
  );
}
