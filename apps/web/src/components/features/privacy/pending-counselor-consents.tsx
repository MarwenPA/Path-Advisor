"use client";

/**
 * <PendingCounselorConsents> — Story 6.7 AC.
 *
 * Rendered above the access-tiers list: for each pending counselor consent
 * request, shows a card + a <ConsentDialog> (Story 1.14) explaining exactly
 * what the counselor will/won't see before the student accepts or refuses.
 */
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ConsentDialog } from "@/components/ui/consent-dialog";
import { ACCESS_LIST_COPY, COUNSELOR_CONSENT_REQUEST_COPY } from "@/lib/i18n/fr/access-list";
import {
  decideCounselorConsent,
  fetchPendingCounselorConsents,
  type PendingCounselorConsent,
} from "@/lib/api/counselor-consent";

const VISIBLE_AREAS = [
  "metiers_explores",
  "parcours_sauvegardes",
  "recommandations",
  "parcoursup_voeux",
  "bulletins_detailles",
  "appreciations_enseignants",
] as const;

export function PendingCounselorConsents() {
  const [consents, setConsents] = useState<PendingCounselorConsent[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "submitting" | "error">("idle");

  useEffect(() => {
    fetchPendingCounselorConsents()
      .then(setConsents)
      .catch(() => undefined);
  }, []);

  async function handleDecide(consentId: string, granted: boolean) {
    setStatus("submitting");
    try {
      await decideCounselorConsent(consentId, granted);
      setConsents((prev) => prev.filter((c) => c.id !== consentId));
      setOpenId(null);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  if (consents.length === 0) return null;

  return (
    <section aria-label="Demandes de ta conseillère" className="flex flex-col gap-3">
      {consents.map((consent) => (
        <div
          key={consent.id}
          className="flex items-center justify-between gap-4 rounded-lg border border-border bg-card p-4"
        >
          <p className="text-body-sm text-text">
            <strong>{consent.counselor_email}</strong> souhaite consulter ton profil.
          </p>
          <Button onClick={() => setOpenId(consent.id)}>Voir la demande</Button>

          <ConsentDialog
            open={openId === consent.id}
            onOpenChange={(next) => setOpenId(next ? consent.id : null)}
            title={COUNSELOR_CONSENT_REQUEST_COPY.title}
            description={COUNSELOR_CONSENT_REQUEST_COPY.description}
            dataMentioned={VISIBLE_AREAS.map((area) => ACCESS_LIST_COPY.dataAreaLabels[area])}
            duration={COUNSELOR_CONSENT_REQUEST_COPY.duration}
            beneficiary={consent.counselor_email}
            acceptLabel={COUNSELOR_CONSENT_REQUEST_COPY.acceptLabel}
            refuseLabel={COUNSELOR_CONSENT_REQUEST_COPY.refuseLabel}
            isSubmitting={status === "submitting"}
            onAccept={() => handleDecide(consent.id, true)}
            onRefuse={() => handleDecide(consent.id, false)}
          />
        </div>
      ))}
      {status === "error" ? (
        <p role="alert" className="text-danger">
          {COUNSELOR_CONSENT_REQUEST_COPY.errorMessage}
        </p>
      ) : null}
    </section>
  );
}
