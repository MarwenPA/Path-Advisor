"use client";

import { FileText, Image as ImageIcon, X } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const MAX_FILES = 6;
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/heic", "image/heif"];

export type PickedFile = { id: string; file: File; error?: string };

type Props = {
  open: boolean;
  files: PickedFile[];
  onFilesChange: (files: PickedFile[]) => void;
  onLaunch: () => void;
  onCancel: () => void;
};

function fileIcon(file: File) {
  if (file.type.startsWith("image/")) {
    return <ImageIcon className="size-4 text-[var(--color-text-muted)]" aria-hidden />;
  }
  return <FileText className="size-4 text-[var(--color-text-muted)]" aria-hidden />;
}

function truncate(name: string, max = 30) {
  if (name.length <= max) return name;
  const ext = name.lastIndexOf(".");
  if (ext > 0) {
    const base = name.slice(0, max - 3 - (name.length - ext));
    return base + "…" + name.slice(ext);
  }
  return name.slice(0, max - 1) + "…";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateFile(file: File, currentCount: number): string | undefined {
  if (file.size > MAX_SIZE_BYTES) {
    return `Trop gros : ce fichier fait ${(file.size / (1024 * 1024)).toFixed(1)} MB, max 10 MB.`;
  }
  const mime = file.type.toLowerCase();
  if (!ALLOWED_TYPES.includes(mime)) {
    return `Format non accepté : ${mime || "inconnu"}. Acceptés : PDF, JPEG, PNG, HEIC.`;
  }
  if (currentCount >= MAX_FILES) {
    return "Maximum 6 fichiers — supprime-en pour en ajouter d'autres.";
  }
  return undefined;
}

export function FilePickerSheet({ open, files, onFilesChange, onLaunch, onCancel }: Props) {
  const photoInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(e.target.files ?? []);
    const newEntries: PickedFile[] = [];
    for (const f of picked) {
      const error = validateFile(f, files.length + newEntries.length);
      newEntries.push({ id: crypto.randomUUID(), file: f, error });
    }
    onFilesChange([...files, ...newEntries]);
    e.target.value = "";
  }

  function removeFile(id: string) {
    onFilesChange(files.filter((f) => f.id !== id));
  }

  const validFiles = files.filter((f) => !f.error);
  const hasError = files.some((f) => f.error);

  return (
    <Sheet open={open} onOpenChange={(isOpen) => { if (!isOpen) onCancel(); }}>
      <SheetContent side="bottom" className="rounded-t-[var(--radius-lg)] max-h-[90dvh] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-[var(--text-h3)]">Tes bulletins</SheetTitle>
          <p className="text-[var(--text-body)] text-[var(--color-text-muted)]">
            Jusqu'à 6 fichiers. PDF, JPEG, PNG ou HEIC.
          </p>
        </SheetHeader>

        {/* Input controls */}
        <div className="flex flex-col gap-3 mt-6">
          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="secondary"
              onClick={() => photoInputRef.current?.click()}
              aria-label="Prendre une photo avec la caméra"
            >
              📷 Prendre en photo
            </Button>
            <Button
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Choisir un fichier dans la galerie ou le disque"
            >
              📂 Choisir un fichier
            </Button>
          </div>

          {/* Hidden file inputs */}
          <input
            ref={photoInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="sr-only"
            onChange={handleInputChange}
            aria-hidden
          />
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="application/pdf,image/jpeg,image/png,image/heic"
            className="sr-only"
            onChange={handleInputChange}
            aria-hidden
          />
        </div>

        {/* File list */}
        {files.length > 0 && (
          <ul className="mt-6 flex flex-col gap-2 list-none p-0" aria-label="Fichiers sélectionnés">
            {files.map((entry) => (
              <li
                key={entry.id}
                className={cn(
                  "flex items-center gap-3 rounded-[var(--radius-md)] border p-3",
                  entry.error
                    ? "border-[var(--color-warning)] bg-[var(--color-warning-bg)]"
                    : "border-[var(--color-border)] bg-[var(--color-bg-2)]"
                )}
              >
                <span className="shrink-0">{fileIcon(entry.file)}</span>
                <span className="flex-1 min-w-0">
                  <span className="block text-sm font-medium text-[var(--color-text)] truncate">
                    {truncate(entry.file.name)}
                  </span>
                  {entry.error ? (
                    <span className="text-xs text-[var(--color-warning)]">{entry.error}</span>
                  ) : (
                    <span className="text-xs text-[var(--color-text-subtle)]">
                      {formatBytes(entry.file.size)}
                    </span>
                  )}
                </span>
                <button
                  type="button"
                  aria-label={`Supprimer ${entry.file.name}`}
                  onClick={() => removeFile(entry.id)}
                  className={cn(
                    "shrink-0 p-2 rounded-[var(--radius-sm)]",
                    "text-[var(--color-text-muted)] hover:text-[var(--color-text)]",
                    "focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]"
                  )}
                >
                  <X className="size-4" aria-hidden />
                </button>
              </li>
            ))}
            <p className="text-xs text-right text-[var(--color-text-subtle)]">
              {validFiles.length}/{MAX_FILES}
            </p>
          </ul>
        )}

        {hasError && (
          <p role="alert" className="mt-2 text-sm text-[var(--color-warning)]">
            Corrige les fichiers en rouge avant de lancer l'analyse.
          </p>
        )}

        <SheetFooter className="mt-6 flex flex-col gap-3">
          <Button
            onClick={onLaunch}
            disabled={validFiles.length === 0 || hasError}
            aria-disabled={validFiles.length === 0 || hasError}
            className="w-full"
          >
            Lancer l'analyse →
          </Button>
          <Button variant="ghost" onClick={onCancel} className="w-full">
            Annuler
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
