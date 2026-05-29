import type { Metadata } from "next";

import { ForgotPasswordForm } from "@/components/features/auth/forgot-password-form";

export const metadata: Metadata = {
  title: "Mot de passe oublié | Path-Advisor",
  description:
    "Réinitialise ton mot de passe Path-Advisor — on t'envoie un lien par email.",
  robots: { index: false, follow: false },
};

export default function ForgotPasswordPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <ForgotPasswordForm />
    </main>
  );
}
