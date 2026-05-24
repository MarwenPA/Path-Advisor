"use client";

import * as React from "react";

import {
  ConsentDialog,
  type ConsentMeta,
} from "@/components/ui/consent-dialog";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  type AccountDeletionRequest,
  getMyAccountDeletionStatus,
  requestAccountDeletion,
} from "@/lib/api/account-deletion";

/*
 * DeleteAccountSection — Story 1.12 §AC10 (+ code-review §D2 follow-up).
 *
 * "Zone dangereuse" section appended to /parametres/confidentialite/mes-donnees.
 * Composes the shared <ConsentDialog> (Story 1.14) — we use its new `bodySlot`
 * prop to embed the inline password input mandated by AC1 ("password input
 * below the description, inline, not a separate step"). The dialog's
 * `onAccept` callback supplies the `ConsentMeta` (acceptedAt + contentHash)
 * which we forward to the backend so the audit row captures exactly what
 * the user saw at decision time (FR12 immutability proof).
 */

const SUCCESS_REDIRECT = "/auth/account-deleted";

const DIALOG_TITLE = "Supprimer définitivement ton compte";
const DIALOG_DESCRIPTION = "Cette action est irréversible passé 30 jours.";
const DIALOG_DATA_MENTIONED = [
  "Profil et bulletins",
  "Recommandations et parcours sauvegardés",
  "Historique d'envois école",
  "Sessions et préférences",
];
const DIALOG_DURATION = "Fenêtre de rétractation : 30 jours";
const DIALOG_BENEFICIARY = "Toi (droit à l'oubli RGPD)";
const DIALOG_ACCEPT_LABEL = "Supprimer mon compte";
const DIALOG_REFUSE_LABEL = "Annuler";

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DeleteAccountSection() {
  const [pending, setPending] = React.useState<AccountDeletionRequest | null>(
    null,
  );
  const [pendingLoading, setPendingLoading] = React.useState(true);
  const [open, setOpen] = React.useState(false);
  const [password, setPassword] = React.useState("");
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const status = await getMyAccountDeletionStatus();
        if (!cancelled) setPending(status);
      } catch (cause) {
        // 404 = no pending request (happy path). Anything else stays silent
        // so a benign API blip doesn't alarm the user.
        if (!(cause instanceof ApiError) || cause.status !== 404) {
          console.warn(
            "[DeleteAccountSection] status check failed:",
            cause,
          );
        }
      } finally {
        if (!cancelled) setPendingLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleOpenChange = React.useCallback(
    (next: boolean) => {
      if (!next && submitting) return; // block close while submitting
      setOpen(next);
      if (!next) {
        setPassword("");
        setSubmitError(null);
      }
    },
    [submitting],
  );

  const handleAccept = React.useCallback(
    async (meta: ConsentMeta) => {
      if (!password) {
        // Defensive: the disabled accept button should prevent this, but
        // belt-and-braces for keyboard-driven submits.
        setSubmitError(
          "Saisis ton mot de passe actuel pour confirmer la suppression.",
        );
        return;
      }
      setSubmitting(true);
      setSubmitError(null);
      try {
        await requestAccountDeletion({
          password,
          contentHash: meta.contentHash,
          acceptedAt: meta.acceptedAt,
        });
        // Hard redirect — the session is dead server-side; full nav avoids
        // hydration mismatches and clears any client-side caches naturally.
        window.location.href = SUCCESS_REDIRECT;
      } catch (cause) {
        const message =
          cause instanceof ApiError
            ? (cause.problem?.detail ?? cause.message)
            : "Une erreur a empêché la suppression. Réessaie dans un instant.";
        setSubmitError(message);
        setPassword("");
        setSubmitting(false);
        // Re-throw so ConsentDialog's internal re-entry guard can release.
        throw cause;
      }
    },
    [password],
  );

  if (pendingLoading) {
    return (
      <section className="flex flex-col gap-3 rounded-lg border border-danger/30 bg-danger/5 p-4">
        <h2 className="text-h2 font-semibold text-text">Zone dangereuse</h2>
        <p className="text-sm text-text-muted" role="status" aria-live="polite">
          Vérification de l&apos;état de ton compte…
        </p>
      </section>
    );
  }

  if (pending) {
    return (
      <section
        aria-labelledby="delete-account-heading"
        className="flex flex-col gap-3 rounded-lg border border-danger/30 bg-danger/5 p-4"
      >
        <h2
          id="delete-account-heading"
          className="text-h2 font-semibold text-text"
        >
          Zone dangereuse
        </h2>
        <p className="text-sm text-text">
          Une demande de suppression de ton compte est en cours. Ton compte
          sera définitivement supprimé le{" "}
          <strong>{formatDateTime(pending.hard_delete_after)}</strong>.
        </p>
        <p className="text-sm text-text-muted">
          Pour annuler, clique sur le lien envoyé dans l&apos;email de
          confirmation (valable jusqu&apos;à cette date).
        </p>
      </section>
    );
  }

  return (
    <section
      aria-labelledby="delete-account-heading"
      className="flex flex-col gap-3 rounded-lg border border-danger/30 bg-danger/5 p-4"
    >
      <h2
        id="delete-account-heading"
        className="text-h2 font-semibold text-text"
      >
        Zone dangereuse
      </h2>
      <p className="text-sm text-text">
        Tu peux demander la suppression complète de ton compte et de toutes
        tes données (droit à l&apos;oubli, RGPD Article 17).
      </p>
      <ul className="list-disc pl-5 text-sm text-text-muted">
        <li>Délai de rétractation : 30 jours après ta demande.</li>
        <li>
          Pendant ces 30 jours, ton compte est désactivé mais récupérable via
          le lien envoyé par email.
        </li>
        <li>
          Au bout des 30 jours, tes données sont effacées définitivement.
          Seul le journal d&apos;audit pseudonymisé est conservé 3 ans
          (obligation légale).
        </li>
      </ul>
      <div>
        <Button
          variant="destructive"
          onClick={() => setOpen(true)}
          aria-haspopup="dialog"
        >
          Supprimer définitivement mon compte
        </Button>
      </div>

      <ConsentDialog
        open={open}
        onOpenChange={handleOpenChange}
        title={DIALOG_TITLE}
        description={DIALOG_DESCRIPTION}
        dataMentioned={DIALOG_DATA_MENTIONED}
        duration={DIALOG_DURATION}
        beneficiary={DIALOG_BENEFICIARY}
        acceptLabel={DIALOG_ACCEPT_LABEL}
        refuseLabel={DIALOG_REFUSE_LABEL}
        isAcceptDestructive
        isSubmitting={submitting}
        isAcceptDisabled={password.length === 0}
        onAccept={handleAccept}
        bodySlot={
          <div className="flex flex-col gap-2">
            <label
              htmlFor="delete-account-password"
              className="text-body-sm font-medium text-text"
            >
              Confirme avec ton mot de passe
            </label>
            <input
              id="delete-account-password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              minLength={1}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              className="rounded-md border border-border bg-background px-3 py-2 text-body text-text focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30"
              aria-describedby={
                submitError ? "delete-account-error" : undefined
              }
            />
            {submitError && (
              <p
                id="delete-account-error"
                role="alert"
                className="text-body-sm text-danger"
              >
                {submitError}
              </p>
            )}
          </div>
        }
      />
    </section>
  );
}
