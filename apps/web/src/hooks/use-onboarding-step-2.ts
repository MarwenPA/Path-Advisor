"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { readCsrfCookie } from "@/lib/api/client";
import {
  fetchOnboardingStep2Snapshot,
  makeEmptyStep2Snapshot,
  patchOnboardingStep2,
  type OnboardingStep2Patch,
  type OnboardingStep2Snapshot,
} from "@/lib/api/onboarding";
import type { NiveauId, FiliereId, Track3emeId, SousFiliereId, PostbacYearId, PostbacFormationId } from "@/lib/onboarding/levels";
import { REF_VERSION, expectedSpecCount, requiresSousFiliere } from "@/lib/onboarding/levels";

const DRAFT_STORAGE_PREFIX = "onboarding_step2_draft";

function draftKeyFor(userId: string | null | undefined): string {
  return userId ? `${DRAFT_STORAGE_PREFIX}:${userId}` : DRAFT_STORAGE_PREFIX;
}

export type Step2Draft = {
  level: NiveauId | null;
  filiere: FiliereId | null;
  sous_filiere_techno: SousFiliereId | null;
  specialites: string[];
  intended_track: Track3emeId | null;
  postbac_year: PostbacYearId | null;
  postbac_formation_type: PostbacFormationId | null;
};

function emptyDraft(): Step2Draft {
  return {
    level: null,
    filiere: null,
    sous_filiere_techno: null,
    specialites: [],
    intended_track: null,
    postbac_year: null,
    postbac_formation_type: null,
  };
}

function readDraft(key: string): Step2Draft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as Step2Draft;
  } catch {
    return null;
  }
}

function writeDraft(key: string, draft: Step2Draft): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(draft));
  } catch {
    // Quota / private mode — silently fall through.
  }
}

function clearDraft(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

function snapshotToDraft(snapshot: OnboardingStep2Snapshot): Step2Draft {
  return {
    level: (snapshot.level as NiveauId) ?? null,
    filiere: (snapshot.filiere as FiliereId) ?? null,
    sous_filiere_techno: (snapshot.sous_filiere_techno as SousFiliereId) ?? null,
    specialites: [...(snapshot.specialites ?? [])],
    intended_track: (snapshot.intended_track as Track3emeId) ?? null,
    postbac_year: (snapshot.postbac_year as PostbacYearId) ?? null,
    postbac_formation_type: (snapshot.postbac_formation_type as PostbacFormationId) ?? null,
  };
}

/** Whether the draft satisfies completion requirements for its branch. */
export function isDraftComplete(draft: Step2Draft): boolean {
  const { level, filiere, sous_filiere_techno, specialites, intended_track, postbac_year, postbac_formation_type } = draft;
  if (!level) return false;
  if (level === "college_3eme") return !!intended_track;
  if (level === "postbac") return !!postbac_year && !!postbac_formation_type;
  // lycee
  if (!filiere) return false;
  if (filiere === "techno" && requiresSousFiliere(level, filiere) && !sous_filiere_techno) return false;
  const expected = expectedSpecCount(level, filiere);
  if (expected !== null && specialites.length !== expected) return false;
  return true;
}

export type UseOnboardingStep2Options = {
  userId: string | null | undefined;
};

export type UseOnboardingStep2Return = {
  snapshot: OnboardingStep2Snapshot;
  draft: Step2Draft;
  isLoading: boolean;
  isSaving: boolean;
  isError: boolean;
  setLevel: (level: NiveauId | null) => void;
  setFiliere: (filiere: FiliereId | null) => void;
  setSousFiliere: (sf: SousFiliereId | null) => void;
  toggleSpecialite: (id: string) => void;
  setIntendedTrack: (track: Track3emeId | null) => void;
  setPostbacYear: (year: PostbacYearId | null) => void;
  setPostbacFormationType: (type: PostbacFormationId | null) => void;
  saveDraft: () => Promise<void>;
  commitLevel: () => Promise<OnboardingStep2Snapshot>;
  skipStep: () => Promise<void>;
  isDraftComplete: boolean;
};

export function useOnboardingStep2({ userId }: UseOnboardingStep2Options): UseOnboardingStep2Return {
  const queryClient = useQueryClient();
  const draftKey = draftKeyFor(userId);

  const { data: snapshot, isLoading, isError } = useQuery({
    queryKey: ["onboarding", "step2", userId],
    queryFn: ({ signal }) => fetchOnboardingStep2Snapshot(signal),
    enabled: !!userId,
    staleTime: 30_000,
  });

  const serverSnapshot = snapshot ?? makeEmptyStep2Snapshot();

  const [draft, setDraft] = React.useState<Step2Draft>(() => {
    // Priority: localStorage draft > server snapshot
    const stored = readDraft(draftKey);
    if (stored) return stored;
    if (snapshot) return snapshotToDraft(snapshot);
    return emptyDraft();
  });

  // Sync draft from server when query resolves for the first time
  React.useEffect(() => {
    if (!snapshot) return;
    const stored = readDraft(draftKey);
    if (!stored) {
      setDraft(snapshotToDraft(snapshot));
    }
  }, [snapshot, draftKey]);

  // Auto-persist on change (debounce 500 ms per AC7)
  const draftRef = React.useRef(draft);
  draftRef.current = draft;
  React.useEffect(() => {
    const tid = setTimeout(() => writeDraft(draftKey, draftRef.current), 500);
    return () => clearTimeout(tid);
  }, [draft, draftKey]);

  const mutation = useMutation({
    mutationFn: async (payload: OnboardingStep2Patch) => {
      const csrf = readCsrfCookie() ?? "";
      return patchOnboardingStep2(payload, csrf);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["onboarding", "step2", userId], data);
    },
  });

  const updateDraft = (partial: Partial<Step2Draft>) => {
    setDraft((prev) => ({ ...prev, ...partial }));
  };

  const setLevel = (level: NiveauId | null) => {
    // Reset branch-specific fields when level changes
    updateDraft({
      level,
      filiere: null,
      sous_filiere_techno: null,
      specialites: [],
      intended_track: null,
      postbac_year: null,
      postbac_formation_type: null,
    });
  };

  const setFiliere = (filiere: FiliereId | null) => {
    // Reset spécialités and sous-filière when filière changes
    updateDraft({ filiere, sous_filiere_techno: null, specialites: [] });
  };

  const setSousFiliere = (sf: SousFiliereId | null) => updateDraft({ sous_filiere_techno: sf });

  const toggleSpecialite = (id: string) => {
    setDraft((prev) => {
      const expected = expectedSpecCount(prev.level!, prev.filiere);
      const isSelected = prev.specialites.includes(id);
      if (isSelected) {
        return { ...prev, specialites: prev.specialites.filter((s) => s !== id) };
      }
      // Reject if already at cap
      if (expected !== null && prev.specialites.length >= expected) return prev;
      return { ...prev, specialites: [...prev.specialites, id] };
    });
  };

  const setIntendedTrack = (track: Track3emeId | null) => updateDraft({ intended_track: track });
  const setPostbacYear = (year: PostbacYearId | null) => updateDraft({ postbac_year: year });
  const setPostbacFormationType = (type: PostbacFormationId | null) =>
    updateDraft({ postbac_formation_type: type });

  const saveDraft = async () => {
    await mutation.mutateAsync({
      ...draft,
      level_ref_version: REF_VERSION,
      commit: false,
    });
  };

  const commitLevel = async (): Promise<OnboardingStep2Snapshot> => {
    const result = await mutation.mutateAsync({
      ...draft,
      level_ref_version: REF_VERSION,
      commit: true,
    });
    clearDraft(draftKey);
    return result;
  };

  const skipStep = async () => {
    await mutation.mutateAsync({ skip: true });
    clearDraft(draftKey);
  };

  return {
    snapshot: serverSnapshot,
    draft,
    isLoading,
    isSaving: mutation.isPending,
    isError,
    setLevel,
    setFiliere,
    setSousFiliere,
    toggleSpecialite,
    setIntendedTrack,
    setPostbacYear,
    setPostbacFormationType,
    saveDraft,
    commitLevel,
    skipStep,
    isDraftComplete: isDraftComplete(draft),
  };
}
