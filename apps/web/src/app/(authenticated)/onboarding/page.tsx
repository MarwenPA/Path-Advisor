import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bienvenue | Path-Advisor",
};

/**
 * Placeholder onboarding page — Story 1.3 (decision §9 #2: Server Component minimal).
 * Story 2.1 will replace this with the real multi-step Zustand-backed flow.
 */
export default function OnboardingPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 bg-bg px-4 py-12 text-center">
      <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
        Bienvenue sur Path-Advisor
      </h1>
      <p className="max-w-md text-body text-text-muted">
        Ton email est vérifié. L’onboarding (passions, intérêts, bulletins…) arrive avec Story 2.1
        (Epic 2). Reviens vite !
      </p>
    </main>
  );
}
