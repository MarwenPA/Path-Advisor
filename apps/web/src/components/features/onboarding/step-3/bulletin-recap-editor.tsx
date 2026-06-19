"use client";

import { AlertTriangle, Plus, Trash2, Undo2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { BulletinRecap, NormalizedField } from "./onboarding-step3-machine";

const LOW_CONF_THRESHOLD = 0.7;

// --- Subject referential (DN4) ---

type SubjectOption = { id: string; name: string };

function useSubjectOptions(): SubjectOption[] {
  const [options, setOptions] = useState<SubjectOption[]>([]);
  useEffect(() => {
    fetch("/api/v1/students/me/subjects-referential", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { subjects?: Array<{ id: string; name: string }> } | null) => {
        if (data?.subjects) setOptions(data.subjects);
      })
      .catch(() => {});
  }, []);
  return options;
}

// --- NoteInput ---

function NoteInput({
  value,
  onChange,
  lowConf,
  rowIndex,
}: {
  value: string;
  onChange: (v: string) => void;
  lowConf: boolean;
  rowIndex: number;
}) {
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  function commit() {
    const num = parseFloat(draft.replace(",", "."));
    if (isNaN(num) || num < 0 || num > 20) {
      setError("Note entre 0 et 20.");
      setDraft(value);
      return;
    }
    setError(null);
    onChange(String(num));
  }

  const errId = `note-err-${rowIndex}`;

  return (
    <span className="flex flex-col gap-0.5">
      <Input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(value);
            setError(null);
          }
        }}
        aria-label="Note sur 20"
        aria-describedby={error ? errId : undefined}
        className={cn("h-7 w-20 text-sm text-center", lowConf && "border-[var(--color-warning)]")}
      />
      {error && (
        <span id={errId} className="text-xs text-[var(--color-danger)]" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}

// --- SubjectRow — returns Fragment with <tr> elements ---

type SubjectRowProps = {
  matiere: NormalizedField;
  note: NormalizedField | undefined;
  appreciation: NormalizedField | undefined;
  rowIndex: number;
  isFirstWarning?: boolean;
  onMatiereChange: (v: string) => void;
  onNoteChange: (v: string) => void;
  onAppreciationChange: (v: string) => void;
  onRemove: () => void;
};

function SubjectRow({
  matiere,
  note,
  appreciation,
  rowIndex,
  isFirstWarning,
  onMatiereChange,
  onNoteChange,
  onAppreciationChange,
  onRemove,
}: SubjectRowProps) {
  const matLowConf = (matiere.confidence ?? 1) < LOW_CONF_THRESHOLD || matiere.isLowConfidence;
  const noteLowConf = note
    ? (note.confidence ?? 1) < LOW_CONF_THRESHOLD || !!note.isLowConfidence
    : false;
  const apprLowConf = appreciation
    ? (appreciation.confidence ?? 1) < LOW_CONF_THRESHOLD || !!appreciation.isLowConfidence
    : false;

  const warnId = `warn-mat-${rowIndex}`;

  return (
    <>
      <tr
        className="border-b border-[var(--color-border)] last:border-0"
        {...(isFirstWarning ? { "data-first-warning": "true" } : {})}
      >
        {/* Matière */}
        <td className="py-2 pr-2 align-top">
          <span className="flex items-center gap-1">
            {matLowConf && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <AlertTriangle
                    className="size-3.5 text-[var(--color-warning)] shrink-0"
                    aria-describedby={warnId}
                  />
                </TooltipTrigger>
                <TooltipContent>À vérifier — l'OCR a un doute sur ce champ</TooltipContent>
              </Tooltip>
            )}
            <span id={warnId} className="sr-only">
              À vérifier
            </span>
            <Input
              value={matiere.value}
              onChange={(e) => onMatiereChange(e.target.value)}
              className="h-7 text-sm"
              aria-label="Matière"
            />
          </span>
        </td>

        {/* Note */}
        <td className="py-2 pr-2 align-top whitespace-nowrap">
          {note ? (
            <span className="flex items-center gap-1">
              {noteLowConf && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertTriangle
                      className="size-3.5 text-[var(--color-warning)]"
                      aria-hidden
                    />
                  </TooltipTrigger>
                  <TooltipContent>À vérifier — l'OCR a un doute sur cette note</TooltipContent>
                </Tooltip>
              )}
              <NoteInput
                value={note.value}
                onChange={onNoteChange}
                lowConf={noteLowConf}
                rowIndex={rowIndex}
              />
              <span className="text-xs text-[var(--color-text-subtle)]">/ 20</span>
            </span>
          ) : (
            <span className="text-xs text-[var(--color-text-muted)]">—</span>
          )}
        </td>

        {/* Delete */}
        <td className="py-2 align-top">
          <button
            type="button"
            aria-label={`Supprimer ${matiere.value}`}
            onClick={onRemove}
            className={cn(
              "p-1 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)]",
              "focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]",
              "min-h-[44px] min-w-[44px] flex items-center justify-center"
            )}
          >
            <Trash2 className="size-4" aria-hidden />
          </button>
        </td>
      </tr>

      {/* Appreciation row */}
      {appreciation && (
        <tr className="border-b border-[var(--color-border)] last:border-0">
          <td colSpan={3} className="pb-2 pt-0">
            <span className="flex items-start gap-1">
              {apprLowConf && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertTriangle
                      className="size-3.5 text-[var(--color-warning)] mt-1.5 shrink-0"
                      aria-hidden
                    />
                  </TooltipTrigger>
                  <TooltipContent>
                    À vérifier — l'OCR a un doute sur cette appréciation
                  </TooltipContent>
                </Tooltip>
              )}
              <Textarea
                value={appreciation.value}
                onChange={(e) => onAppreciationChange(e.target.value)}
                rows={2}
                className={cn(
                  "text-sm resize-none flex-1",
                  apprLowConf && "border-[var(--color-warning)]"
                )}
                aria-label={`Appréciation de ${matiere.value}`}
              />
            </span>
          </td>
        </tr>
      )}
    </>
  );
}

// --- AddSubjectRow (DN4) ---

function AddSubjectRow({
  subjectOptions,
  onConfirm,
  onCancel,
}: {
  subjectOptions: SubjectOption[];
  onConfirm: (name: string, canonicalId?: string) => void;
  onCancel: () => void;
}) {
  const [selected, setSelected] = useState<string>("");
  const [freeText, setFreeText] = useState("");
  const showFreeText = selected === "__custom__" || subjectOptions.length === 0;

  function handleConfirm() {
    if (showFreeText) {
      const name = freeText.trim();
      if (!name) return;
      onConfirm(name);
    } else {
      const opt = subjectOptions.find((o) => o.id === selected);
      if (!opt) return;
      onConfirm(opt.name, opt.id);
    }
  }

  return (
    <>
      <tr>
        <td className="py-2 pr-2" colSpan={2}>
          {subjectOptions.length > 0 ? (
            <span className="flex flex-col gap-1">
              <Select value={selected} onValueChange={setSelected}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="Choisir une matière…" />
                </SelectTrigger>
                <SelectContent>
                  {subjectOptions.map((o) => (
                    <SelectItem key={o.id} value={o.id}>
                      {o.name}
                    </SelectItem>
                  ))}
                  <SelectItem value="__custom__">Autre (saisir)…</SelectItem>
                </SelectContent>
              </Select>
              {showFreeText && (
                <Input
                  autoFocus
                  value={freeText}
                  onChange={(e) => setFreeText(e.target.value)}
                  placeholder="Nom de la matière"
                  className="h-7 text-sm"
                  aria-label="Nom de la matière"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleConfirm();
                    if (e.key === "Escape") onCancel();
                  }}
                />
              )}
            </span>
          ) : (
            <Input
              autoFocus
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder="Nom de la matière"
              className="h-7 text-sm"
              aria-label="Nom de la matière"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleConfirm();
                if (e.key === "Escape") onCancel();
              }}
            />
          )}
        </td>
        <td className="py-2 align-top">
          <span className="flex gap-1">
            <Button size="sm" className="h-7 px-2 text-xs" onClick={handleConfirm}>
              OK
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-xs"
              onClick={onCancel}
            >
              Annuler
            </Button>
          </span>
        </td>
      </tr>
    </>
  );
}

// --- BulletinRecapEditor ---

type Props = {
  recaps: BulletinRecap[];
  activeIndex: number;
  onActiveChange: (index: number) => void;
  onFieldsChange: (bulletinId: string, fields: NormalizedField[]) => void;
  onValidate: (bulletinId: string) => void;
  onAllValidated: () => void;
};

type UndoEntry = {
  bulletinId: string;
  removedFields: NormalizedField[];
  label: string;
  timeoutId: ReturnType<typeof setTimeout>;
};

export function BulletinRecapEditor({
  recaps,
  activeIndex,
  onActiveChange,
  onFieldsChange,
  onValidate,
  onAllValidated,
}: Props) {
  const recap = recaps[activeIndex];
  const activeFields = recap?.draftFields ?? recap?.fields ?? [];
  const subjectOptions = useSubjectOptions();

  const [isAddingSubject, setIsAddingSubject] = useState(false);
  const [undoEntry, setUndoEntry] = useState<UndoEntry | null>(null);

  const lowConfCount = activeFields.filter(
    (f) => f.confidence < LOW_CONF_THRESHOLD || f.isLowConfidence
  ).length;

  const matieres = activeFields.filter((f) => f.key === "matiere");
  const allValidated = recaps.every((r) => r.validated);

  const tableRef = useRef<HTMLTableElement>(null);

  function scrollToFirstWarning() {
    const el = tableRef.current?.querySelector<HTMLElement>("[data-first-warning]");
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    (el?.querySelector("input") as HTMLInputElement | null)?.focus();
  }

  function getNoteForMatiere(matiereIndex: number): NormalizedField | undefined {
    let mIdx = -1;
    let found = false;
    for (const f of activeFields) {
      if (f.key === "matiere") {
        mIdx++;
        found = mIdx === matiereIndex;
      } else if (f.key === "note" && found) {
        return f;
      }
    }
    return undefined;
  }

  function getAppreciationForMatiere(matiereIndex: number): NormalizedField | undefined {
    let mIdx = -1;
    let found = false;
    for (const f of activeFields) {
      if (f.key === "matiere") {
        mIdx++;
        found = mIdx === matiereIndex;
      } else if (f.key === "appreciation" && found) {
        return f;
      }
    }
    return undefined;
  }

  function handleMatiereChange(matiereIndex: number, newValue: string) {
    let mIdx = -1;
    const newFields = activeFields.map((f) => {
      if (f.key === "matiere") {
        mIdx++;
        if (mIdx === matiereIndex) return { ...f, value: newValue };
      }
      return f;
    });
    onFieldsChange(recap.bulletinId, newFields);
  }

  function handleNoteChange(matiereIndex: number, newValue: string) {
    let mIdx = -1;
    let captured = false;
    const newFields = activeFields.map((f) => {
      if (f.key === "matiere") {
        mIdx++;
        captured = mIdx === matiereIndex;
        return f;
      }
      if (f.key === "note" && captured) {
        captured = false;
        return { ...f, value: newValue, confidence: 1.0 };
      }
      return f;
    });
    onFieldsChange(recap.bulletinId, newFields);
  }

  function handleAppreciationChange(matiereIndex: number, newValue: string) {
    let mIdx = -1;
    let captured = false;
    const newFields = activeFields.map((f) => {
      if (f.key === "matiere") {
        mIdx++;
        captured = mIdx === matiereIndex;
        return f;
      }
      if (f.key === "appreciation" && captured) {
        captured = false;
        return { ...f, value: newValue };
      }
      return f;
    });
    onFieldsChange(recap.bulletinId, newFields);
  }

  function handleRemoveMatiere(matiereIndex: number) {
    let mIdx = -1;
    let skip = false;
    const removed: NormalizedField[] = [];
    const newFields = activeFields.filter((f) => {
      if (f.key === "matiere") {
        mIdx++;
        skip = mIdx === matiereIndex;
        if (skip) { removed.push(f); return false; }
      }
      if (skip && (f.key === "note" || f.key === "appreciation")) {
        removed.push(f);
        return false;
      }
      skip = false;
      return true;
    });
    onFieldsChange(recap.bulletinId, newFields);

    // Undo toast
    if (undoEntry) clearTimeout(undoEntry.timeoutId);
    const label = removed.find((f) => f.key === "matiere")?.value ?? "matière";
    const timeoutId = setTimeout(() => setUndoEntry(null), 5000);
    setUndoEntry({ bulletinId: recap.bulletinId, removedFields: removed, label, timeoutId });
  }

  function handleUndo() {
    if (!undoEntry) return;
    clearTimeout(undoEntry.timeoutId);
    // Restore: append removed fields back
    const current = recap.draftFields ?? recap.fields ?? [];
    onFieldsChange(undoEntry.bulletinId, [...current, ...undoEntry.removedFields]);
    setUndoEntry(null);
  }

  function handleAddSubject(name: string, canonicalId?: string) {
    const newFields: NormalizedField[] = [
      ...activeFields,
      {
        key: "matiere",
        value: name,
        confidence: 1.0,
        canonical_id: canonicalId ?? null,
      },
      { key: "note", value: "0", confidence: 1.0 },
    ];
    onFieldsChange(recap.bulletinId, newFields);
    setIsAddingSubject(false);
  }

  if (!recap) return null;

  return (
    <section aria-label="Récapitulatif des bulletins" className="flex flex-col gap-4">
      <h2 className="text-[var(--text-h2)] font-semibold text-[var(--color-text)]">
        Voilà ce qu'on a lu
      </h2>
      <p className="text-[var(--text-body)] text-[var(--color-text-muted)]">
        Corrige si besoin — on peut se tromper. Toi seul·e sais ce qui est juste.
      </p>

      {lowConfCount > 0 && (
        <div className="flex items-center gap-2 text-sm text-[var(--color-warning)]">
          <AlertTriangle className="size-4" aria-hidden />
          <span>
            {lowConfCount} champ{lowConfCount > 1 ? "s" : ""} à vérifier
          </span>
          <button
            type="button"
            onClick={scrollToFirstWarning}
            className="ml-1 underline underline-offset-2 text-[var(--color-brand)]"
          >
            Voir les champs
          </button>
        </div>
      )}

      {recaps.length > 1 && (
        <Tabs
          value={String(activeIndex)}
          onValueChange={(v) => onActiveChange(Number(v))}
        >
          <TabsList>
            {recaps.map((r, i) => (
              <TabsTrigger key={r.bulletinId} value={String(i)}>
                {r.label}
                {r.validated && (
                  <span className="ml-1 text-[var(--color-brand)]" aria-label="Validé">
                    ✓
                  </span>
                )}
              </TabsTrigger>
            ))}
          </TabsList>
          {recaps.map((r, i) => (
            <TabsContent key={r.bulletinId} value={String(i)} />
          ))}
        </Tabs>
      )}

      {/* Subject table — valid HTML: no <ul> inside <tbody> */}
      <div className="overflow-x-auto">
        <table ref={tableRef} className="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th scope="col" className="text-left text-xs font-medium text-[var(--color-text-muted)] pb-1">
                Matière
              </th>
              <th scope="col" className="text-left text-xs font-medium text-[var(--color-text-muted)] pb-1">
                Note
              </th>
              <th scope="col">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {matieres.length === 0 && !isAddingSubject && (
              <tr>
                <td
                  colSpan={3}
                  className="text-center text-[var(--color-text-muted)] py-6 text-sm"
                >
                  Aucune matière — commence par en ajouter une ci-dessous.
                </td>
              </tr>
            )}
            {matieres.map((m, matiereIndex) => {
              const note = getNoteForMatiere(matiereIndex);
              const appr = getAppreciationForMatiere(matiereIndex);
              const isLowConf = m.confidence < LOW_CONF_THRESHOLD || m.isLowConfidence;
              return (
                <SubjectRow
                  key={`subj-${matiereIndex}`}
                  isFirstWarning={isLowConf && matiereIndex === 0}
                  matiere={m}
                  note={note}
                  appreciation={appr}
                  rowIndex={matiereIndex}
                  onMatiereChange={(v) => handleMatiereChange(matiereIndex, v)}
                  onNoteChange={(v) => handleNoteChange(matiereIndex, v)}
                  onAppreciationChange={(v) => handleAppreciationChange(matiereIndex, v)}
                  onRemove={() => handleRemoveMatiere(matiereIndex)}
                />
              );
            })}
            {isAddingSubject && (
              <AddSubjectRow
                subjectOptions={subjectOptions}
                onConfirm={handleAddSubject}
                onCancel={() => setIsAddingSubject(false)}
              />
            )}
          </tbody>
        </table>
      </div>

      {/* Undo toast */}
      {undoEntry && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] bg-[var(--color-bg-subtle)] border border-[var(--color-border)] rounded-md px-3 py-2"
        >
          <Undo2 className="size-4 shrink-0" aria-hidden />
          <span>« {undoEntry.label} » supprimé</span>
          <button
            type="button"
            onClick={handleUndo}
            className="ml-auto text-[var(--color-brand)] underline underline-offset-2 text-xs focus-visible:outline-[var(--color-brand)]"
          >
            Annuler
          </button>
        </div>
      )}

      <Button
        variant="ghost"
        size="sm"
        className="self-start text-[var(--color-brand)]"
        onClick={() => setIsAddingSubject(true)}
        disabled={isAddingSubject}
      >
        <Plus className="size-4 mr-1" aria-hidden />
        Ajouter une matière manquante
      </Button>

      <div className="sticky bottom-0 bg-[var(--color-bg)] pt-4 pb-6 border-t border-[var(--color-border)]">
        {allValidated ? (
          <Button onClick={onAllValidated} className="w-full" size="lg">
            Terminer l'onboarding →
          </Button>
        ) : (
          <Button
            onClick={() => onValidate(recap.bulletinId)}
            disabled={recap.validated || matieres.length === 0}
            className="w-full"
            size="lg"
          >
            {recap.validated ? "✓ Trimestre validé" : "Valider ce trimestre →"}
          </Button>
        )}
      </div>
    </section>
  );
}
