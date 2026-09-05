import type { Metadata } from "next";

import { CounselorInvitationForm } from "@/components/features/establishments/counselor-invitation-form";
import { fetchCounselorInvitationStatus } from "@/lib/api/establishments";
import type { CounselorInvitationPublicStatus } from "@/lib/api/establishments";

export const metadata: Metadata = {
  title: "Accès conseillère | Path-Advisor",
  robots: { index: false, follow: false },
};

// Story 6.1 §T6 pattern — always render fresh, token state can change between clicks.
export const dynamic = "force-dynamic";

/**
 * Code-review fix (2026-09-05, closing out Story 6.5): this used to be a
 * bare `fetch()` reading `process.env.API_BASE_URL` — a variable that is
 * never actually set anywhere (docker-compose sets `API_URL_SERVER` for
 * server-side calls, `NEXT_PUBLIC_API_URL` for the browser — see
 * `lib/api/client.ts`). It silently fell back to the hardcoded
 * `http://localhost:8000`, which is unreachable from inside the `web`
 * container in Docker (that's the container's own loopback, not the `api`
 * service) — every visit to `/auth/invitation-conseillere/{token}` would
 * `catch` the fetch failure and render "Ce lien n'est plus valide" even
 * for a genuinely valid, pending invitation. Routed through the existing
 * `fetchCounselorInvitationStatus` (uses `apiFetch`, which resolves the
 * correct host for both server and browser contexts) instead of
 * duplicating fetch logic with the wrong host.
 */
async function fetchStatus(token: string): Promise<CounselorInvitationPublicStatus | null> {
  try {
    return await fetchCounselorInvitationStatus(token);
  } catch {
    return null;
  }
}

export default async function InvitationConseillerePage({
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
          Le lien d&apos;invitation a expiré ou a déjà été utilisé. Contacte l&apos;équipe
          Path-Advisor pour en recevoir un nouveau.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <p className="text-body-sm uppercase tracking-wide text-text-muted">
          Invitation de {status.establishment_name}
        </p>
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          Créer mon compte conseillère
        </h1>
        <p className="text-body text-text-muted">{status.email}</p>
      </header>
      <CounselorInvitationForm token={token} />
    </main>
  );
}
