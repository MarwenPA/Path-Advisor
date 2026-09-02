import type { Metadata } from "next";

import { StudentInvitationForm } from "@/components/features/establishments/student-invitation-form";
import type { StudentInvitationPublicStatus } from "@/lib/api/establishments";

export const metadata: Metadata = {
  title: "Activer mon compte | Path-Advisor",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

async function fetchStatus(token: string): Promise<StudentInvitationPublicStatus | null> {
  const apiBase = process.env.API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${apiBase}/api/v1/students/invitation/${encodeURIComponent(token)}/`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return (await res.json()) as StudentInvitationPublicStatus;
  } catch {
    return null;
  }
}

export default async function InvitationElevePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const status = await fetchStatus(token);

  if (!status || status.status !== "pending") {
    return (
      <main className="mx-auto flex w-full max-w-lg flex-col gap-4 px-4 py-16 text-center">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          Ce lien n&apos;est plus valide
        </h1>
        <p className="text-body text-text-muted">
          Le lien d&apos;activation a expiré ou a déjà été utilisé. Contacte ton établissement pour
          en recevoir un nouveau.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <p className="text-body-sm uppercase tracking-wide text-text-muted">
          {status.establishment_name}
        </p>
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          Activer mon compte Path-Advisor
        </h1>
      </header>
      <StudentInvitationForm token={token} />
    </main>
  );
}
