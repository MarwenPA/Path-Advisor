import type { Metadata } from "next";

import { MfaSettingsForm } from "@/components/features/auth/mfa-settings-form";
import { fetchCurrentUser } from "@/lib/api/auth";

export const metadata: Metadata = {
  title: "Sécurité — Double authentification | Path-Advisor",
  description: "Gère ta double authentification (MFA TOTP) et tes codes de récupération.",
};

export default async function MfaSettingsPage() {
  // Server Component — fetch the current user so the dashboard reflects the
  // latest state (mfa_enrolled, recovery_codes_remaining) without a client
  // round-trip on mount.
  const user = await fetchCurrentUser();

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          Double authentification
        </h1>
        <p className="text-body text-text-muted">
          Ajoute une étape de vérification supplémentaire à ton compte en plus de ton mot de passe.
          Pour les rôles staff (conseiller, école, admin) c&apos;est obligatoire ; pour les élèves
          et parents c&apos;est optionnel mais fortement recommandé.
        </p>
      </header>

      <MfaSettingsForm user={user} />
    </main>
  );
}
