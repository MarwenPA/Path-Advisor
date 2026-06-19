"use client";

import * as React from "react";

import type { MaturityLevel } from "@/lib/profile/maturity";

// ---------------------------------------------------------------------------
// Celebration messages — locked per AC8 (discreet, no confetti, no modal)
// ---------------------------------------------------------------------------

const CELEBRATION_MESSAGES: Partial<Record<MaturityLevel, string>> = {
  enriched:
    "Profil enrichi débloqué — tes stats sont maintenant personnalisées.",
  complete:
    "Profil complet débloqué — tu profites de toutes les features.",
};

const STORAGE_PREFIX = "maturity_prev_level";

function storageKey(userId: string): string {
  return `${STORAGE_PREFIX}:${userId}`;
}

export interface MaturityCelebration {
  message: string | null;
  dismiss: () => void;
}

/**
 * Detects upward maturity transitions and returns a one-shot toast message.
 *
 * Rules (AC8):
 * - Only 'base → enriched' and 'enriched → complete' trigger a message.
 * - No message on downgrade (silence respectueux).
 * - Each transition fires at most once per session (sessionStorage).
 * - Server-side dedup flag is set via PATCH on celebration seen (fire-and-forget).
 */
export function useMaturityCelebration(
  currentLevel: MaturityLevel | undefined,
  userId: string | null | undefined
): MaturityCelebration {
  const [message, setMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!currentLevel || !userId) return;

    const key = storageKey(userId);
    const prev = (sessionStorage.getItem(key) ?? null) as MaturityLevel | null;

    const isLevelUp =
      (prev === "base" && currentLevel === "enriched") ||
      (prev === "base" && currentLevel === "complete") ||
      (prev === "enriched" && currentLevel === "complete");

    if (isLevelUp) {
      const celebMsg = CELEBRATION_MESSAGES[currentLevel];
      if (celebMsg) {
        setMessage(celebMsg);
        // Mark as seen for this session so returning to the page doesn't re-fire
        sessionStorage.setItem(key, currentLevel);
        // Fire-and-forget: mark server-side flag so it doesn't fire again across sessions
        void markCelebrationSeen(currentLevel, userId);
      }
    } else {
      // Always update stored level (including downgrades — silently)
      sessionStorage.setItem(key, currentLevel);
    }
  }, [currentLevel, userId]);

  const dismiss = React.useCallback(() => setMessage(null), []);

  return { message, dismiss };
}

async function markCelebrationSeen(level: MaturityLevel, _userId: string): Promise<void> {
  try {
    await fetch("/api/v1/students/me/profile/maturity/celebration", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level }),
    });
  } catch {
    // Silently swallow — this is analytics, not user-critical
  }
}
