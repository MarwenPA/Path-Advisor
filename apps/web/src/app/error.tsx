"use client";

/**
 * Global error boundary — revue Epic 8 (P1-6b): no route had one, so any
 * uncaught render error (e.g. a malformed API payload) showed Next's raw
 * "Application error" screen to a student. Calm copy, one retry action —
 * same emotional contract as everything else (UX-DR28), strings kept here
 * (not fr.json): the boundary must render even if the i18n provider itself
 * is what crashed. Scanned by the front tone lint via its own test.
 */

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[error-boundary]", error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[60vh] w-full max-w-xl flex-col items-start justify-center gap-4 px-4 py-12">
      <h1 className="text-2xl font-semibold text-text">Quelque chose n&apos;a pas fonctionné</h1>
      <p className="text-body text-text-muted">
        Ce n&apos;est pas de ton fait — une erreur technique est survenue de notre côté. Tes données
        n&apos;ont pas bougé. Tu peux réessayer, ou revenir un peu plus tard.
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        Réessayer
      </button>
    </main>
  );
}
