"use client";

import { useCallback, useEffect, useState } from "react";

export interface MatiereDraft {
  subject_id: string;
  note: number | null;
  appreciation: string | null;
  is_custom?: boolean;
}

const DEBOUNCE_MS = 500;

function storageKey(trimestreId: string): string {
  return `manual_bulletin_draft_${trimestreId}`;
}

export function useManualBulletinDraft(trimestreId: string) {
  const [drafts, setDrafts] = useState<MatiereDraft[]>(() => {
    if (typeof window === "undefined") return [];
    const raw = window.localStorage.getItem(storageKey(trimestreId));
    if (!raw) return [];
    try {
      return JSON.parse(raw) as MatiereDraft[];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    const id = setTimeout(() => {
      window.localStorage.setItem(storageKey(trimestreId), JSON.stringify(drafts));
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [drafts, trimestreId]);

  const updateDraft = useCallback(
    (subjectId: string, updates: Partial<MatiereDraft>) => {
      setDrafts((prev) => {
        const idx = prev.findIndex((d) => d.subject_id === subjectId);
        if (idx === -1) {
          return [...prev, { subject_id: subjectId, note: null, appreciation: null, ...updates }];
        }
        const updated = [...prev];
        updated[idx] = { ...updated[idx], ...updates };
        return updated;
      });
    },
    []
  );

  const removeDraft = useCallback((subjectId: string) => {
    setDrafts((prev) => prev.filter((d) => d.subject_id !== subjectId));
  }, []);

  const flushDraft = useCallback(() => {
    window.localStorage.removeItem(storageKey(trimestreId));
  }, [trimestreId]);

  return { drafts, updateDraft, removeDraft, flushDraft };
}
