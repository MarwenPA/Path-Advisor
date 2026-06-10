import type { Metadata } from "next";

import { MfaEnrollForm } from "@/components/features/auth/mfa-enroll-form";

export const metadata: Metadata = {
  title: "Configurer la double authentification | Path-Advisor",
  description: "Configure ton authenticator TOTP pour sécuriser ton compte Path-Advisor.",
  robots: { index: false, follow: false },
};

export default function MfaEnrollPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <MfaEnrollForm />
    </main>
  );
}
