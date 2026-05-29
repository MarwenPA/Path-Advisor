import type { Metadata } from "next";

import { ResetPasswordForm } from "@/components/features/auth/reset-password-form";

export const metadata: Metadata = {
  title: "Nouveau mot de passe | Path-Advisor",
  description: "Choisis un nouveau mot de passe pour ton compte Path-Advisor.",
  robots: { index: false, follow: false },
};

interface PageProps {
  params: Promise<{ uid: string; token: string }>;
}

export default async function ResetPasswordPage({ params }: PageProps) {
  // Next.js 15 — dynamic route params are async per the App Router contract.
  const { uid, token } = await params;
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <ResetPasswordForm uid={uid} token={token} />
    </main>
  );
}
