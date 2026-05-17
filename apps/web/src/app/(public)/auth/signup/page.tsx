import type { Metadata } from "next";

import { SignupForm } from "@/components/features/auth/signup-form";

export const metadata: Metadata = {
  title: "Créer un compte | Path-Advisor",
  description:
    "Inscris-toi à Path-Advisor en moins d'une minute. Découvre des métiers et des parcours adaptés à ton profil, en toute transparence.",
};

export default function SignupPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <SignupForm />
    </main>
  );
}
