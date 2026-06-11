import { OnboardingStep1 } from "@/components/features/onboarding/onboarding-step-1";

/**
 * `/onboarding/step-1` — Story 2.1 entry point. The (authenticated) layout
 * already enforces auth + role guard (`/onboarding/*` → `["student"]` per
 * Story 1.7 ROUTE_ALLOWED_ROLES), so this page only renders the client
 * orchestrator. The orchestrator handles the runtime AC10 redirect to
 * step-2 when the snapshot reports `onboarding_step1_status === "completed"`.
 */
export const metadata = {
  title: "Onboarding — Tes passions, valeurs et centres d'intérêt | Path-Advisor",
};

export default function OnboardingStep1Page() {
  return <OnboardingStep1 />;
}
