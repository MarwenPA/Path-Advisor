"use client";

/**
 * /parametres/mes-proches — Story 6.1 §T7.1.
 *
 * Élève-side view to INVITE / RESEND parent invitations. Distinct from
 * `/parametres/confidentialite/acces-tiers` (Story 1.9) which is the
 * cross-tier AUDIT/REVOKE surface — the two pages complement each other
 * (cf. story §4.1).
 */
import { useEffect, useState } from "react";

import { InviteParentDialog } from "@/components/features/family/invite-parent-dialog";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  fetchParentInvitations,
  resendParentInvitation,
  type ParentInvitation,
} from "@/lib/api/family";
import { FAMILY_COPY } from "@/lib/i18n/fr/family";

export default function MesProchesPage() {
  const [invitations, setInvitations] = useState<ParentInvitation[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchParentInvitations();
      setInvitations(data);
    } catch {
      setInvitations([]);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch — runs once on mount. `load` is async and only calls
  // setState after its await, matching the repo's established pattern
  // (cf. gdpr-export-list.tsx).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, []);

  const handleInvited = (email: string) => {
    setToast(FAMILY_COPY.toastInvitationSent(email));
    void load();
  };

  const handleResend = async (invitationId: string) => {
    try {
      await resendParentInvitation(invitationId);
      setToast("Invitation renvoyée.");
    } catch (err) {
      if (err instanceof ApiError) {
        setToast(err.problem?.detail ?? "Le renvoi a échoué.");
      }
    }
  };

  return (
    <main
      className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-12"
      aria-labelledby="mes-proches-title"
    >
      <header className="flex flex-col gap-2">
        <h1 id="mes-proches-title" className="text-h1 font-semibold text-text md:text-h1-desktop">
          {FAMILY_COPY.pageTitle}
        </h1>
        <p className="text-body text-text-muted">{FAMILY_COPY.pageDescription}</p>
      </header>

      <InviteParentDialog onInvited={handleInvited} />

      {toast ? (
        <p role="status" aria-live="polite" className="text-sm text-text-muted">
          {toast}
        </p>
      ) : null}

      <section aria-live="polite" className="flex flex-col gap-4">
        {!loading && invitations.length === 0 ? (
          <p className="text-body text-text-muted">{FAMILY_COPY.emptyState}</p>
        ) : null}
        {invitations.map((invitation) => (
          <article
            key={invitation.id}
            className="flex items-center justify-between rounded-md border border-border p-4"
          >
            <div>
              <p className="text-body font-medium text-text">{invitation.parent_email}</p>
              <p className="text-body-sm text-text-muted">
                {FAMILY_COPY.statusLabels[invitation.status]}
              </p>
            </div>
            {invitation.status === "pending" ? (
              <Button variant="outline" onClick={() => void handleResend(invitation.id)}>
                {FAMILY_COPY.resendButtonLabel}
              </Button>
            ) : null}
          </article>
        ))}
      </section>
    </main>
  );
}
