"use client";

/**
 * Private notes panel for the counselor individual profile view — Story 6.8
 * AC2. Notes are private to the authoring counselor (never student- or
 * peer-counselor-readable — enforced server-side, this component just
 * renders what the API already scoped).
 */
import { useState, useTransition } from "react";

import { addCounselorNote, type CounselorNote } from "@/lib/api/counselor-profile";

export function CounselorNotesPanel({
  studentId,
  initialNotes,
}: {
  studentId: string;
  initialNotes: CounselorNote[];
}) {
  const [notes, setNotes] = useState(initialNotes);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    setError(null);
    startTransition(async () => {
      try {
        const note = await addCounselorNote(studentId, trimmed);
        setNotes((prev) => [note, ...prev]);
        setText("");
      } catch {
        setError("Impossible d'enregistrer la note. Réessayez.");
      }
    });
  }

  return (
    <section className="rounded-lg border border-border bg-card p-4">
      <h2 className="mb-3 text-h3 font-semibold text-text">Notes personnelles</h2>
      <p className="mb-3 text-caption text-text-subtle">
        Visibles uniquement par vous — jamais par l&apos;élève ni les autres conseillères.
      </p>

      <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={4000}
          rows={3}
          placeholder="Ajouter une note…"
          className="rounded-lg border border-border bg-background p-2 text-body-sm text-text"
        />
        {error && <p className="text-body-sm text-danger">{error}</p>}
        <button
          type="submit"
          disabled={isPending || !text.trim()}
          className="self-end rounded-lg bg-primary px-3 py-1.5 text-body-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {isPending ? "Enregistrement…" : "Ajouter"}
        </button>
      </form>

      {notes.length === 0 ? (
        <p className="text-body-sm text-text-muted">Aucune note pour l&apos;instant.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {notes.map((note) => (
            <li key={note.id} className="border-b border-border pb-2 text-body-sm text-text">
              <p className="whitespace-pre-wrap">{note.text}</p>
              <p className="mt-1 text-caption text-text-subtle">
                {new Date(note.created_at).toLocaleString("fr-FR")}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
