import type { Metadata } from "next";

import { MfaChallengeForm } from "@/components/features/auth/mfa-challenge-form";

export const metadata: Metadata = {
  title: "Vérification double authentification | Path-Advisor",
  description:
    "Saisis ton code TOTP ou un code de récupération pour finaliser ta connexion.",
  robots: { index: false, follow: false },
};

export default function MfaChallengePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <MfaChallengeForm />
    </main>
  );
}
