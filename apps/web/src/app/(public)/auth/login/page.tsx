import type { Metadata } from "next";
import Link from "next/link";

import { LoginForm } from "@/components/features/auth/login-form";
import { LogoWordmark } from "@/components/ui/logo";

export const metadata: Metadata = {
  title: "Connexion | Path-Advisor",
  description: "Connecte-toi à ton espace Path-Advisor.",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-8 bg-bg px-4 py-12">
      <Link href="/" aria-label="Path-Advisor, accueil">
        <LogoWordmark />
      </Link>
      <LoginForm />
    </main>
  );
}
