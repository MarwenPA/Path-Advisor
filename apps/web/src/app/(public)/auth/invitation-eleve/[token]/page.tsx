import type { Metadata } from "next";

import { StudentInvitationForm } from "@/components/features/establishments/student-invitation-form";
import { fetchStudentInvitationStatus } from "@/lib/api/establishments";
import type { StudentInvitationPublicStatus } from "@/lib/api/establishments";

export const metadata: Metadata = {
  title: "Activer mon compte | Path-Advisor",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

// Code-review fix (2026-09-05, closing out Story 6.5) — same wrong-host bug
// as the counselor invitation page: this used to read the never-set
// `process.env.API_BASE_URL` and silently fall back to
// `http://localhost:8000`, unreachable from inside the `web` container.
// Routed through `fetchStudentInvitationStatus` (`apiFetch`, correct host
// resolution for both server and browser).
async function fetchStatus(token: string): Promise<StudentInvitationPublicStatus | null> {
  try {
    return await fetchStudentInvitationStatus(token);
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
