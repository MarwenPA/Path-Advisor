"use client";

import { useState } from "react";
import { ChevronDown, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { MatiereDef } from "@/lib/onboarding/subjects-by-level";

interface MatiereInputRowProps {
  subject: MatiereDef;
  note: number | null;
  appreciation: string | null;
  onNoteChange: (subjectId: string, note: number) => void;
  onAppreciationChange: (subjectId: string, appreciation: string) => void;
  onRemove: (subjectId: string) => void;
}

function parseNote(raw: string): number | "error" | "empty" {
  if (!raw.trim()) return "empty";
  const normalized = raw.replace(",", ".");
  const n = parseFloat(normalized);
  if (isNaN(n) || n < 0 || n > 20) return "error";
  return Math.round(n * 100) / 100;
}

export function MatiereInputRow({
  subject,
  note,
  appreciation,
  onNoteChange,
  onAppreciationChange,
  onRemove,
}: MatiereInputRowProps) {
  const [inputValue, setInputValue] = useState(note !== null ? String(note) : "");
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  function handleBlur() {
    const result = parseNote(inputValue);
    if (result === "empty") {
      setError(null);
      return;
    }
    if (result === "error") {
      setError("Note entre 0 et 20");
      return;
    }
    setError(null);
    onNoteChange(subject.id, result);
  }

  return (
    <fieldset className="py-3 border-b border-border last:border-0">
      <legend className="sr-only">{subject.label}</legend>

      <div className="flex items-center gap-3">
        <span className="flex-1 text-sm font-medium">{subject.label}</span>

        <div className="flex items-center gap-2">
          <div className="w-[88px] relative">
            <Input
              type="text"
              inputMode="decimal"
              placeholder="—.— / 20"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onBlur={handleBlur}
              aria-invalid={!!error}
              aria-describedby={error ? `${subject.id}-error` : undefined}
              className={cn(
                "text-right tabular-nums",
                error && "border-destructive"
              )}
            />
          </div>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            aria-label="Ajouter une appréciation"
            className="text-xs text-muted-foreground gap-1 px-2"
          >
            {expanded ? "▲" : "+"} Appréciation
            <ChevronDown
              size={12}
              className={cn("transition-transform", expanded && "rotate-180")}
              aria-hidden="true"
            />
          </Button>

          <button
            type="button"
            aria-label={`Supprimer ${subject.label}`}
            onClick={() => onRemove(subject.id)}
            className="text-muted-foreground hover:text-foreground p-1"
          >
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      </div>

      {error && (
        <span
          id={`${subject.id}-error`}
          role="alert"
          aria-live="polite"
          className="text-xs text-destructive mt-1 block"
        >
          {error}
        </span>
      )}

      {expanded && (
        <Textarea
          aria-label="Appréciation"
          rows={3}
          maxLength={500}
          value={appreciation ?? ""}
          onChange={(e) => onAppreciationChange(subject.id, e.target.value)}
          placeholder="Appréciation du professeur (facultatif)"
          className="mt-2 text-sm"
        />
      )}
    </fieldset>
  );
}
