import type { Metadata } from "next";

import { LoginForm } from "@/components/features/auth/login-form";

export const metadata: Metadata = {
  title: "Connexion | Path-Advisor",
  description: "Connecte-toi à ton espace Path-Advisor.",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <LoginForm />
    </main>
  );
}
