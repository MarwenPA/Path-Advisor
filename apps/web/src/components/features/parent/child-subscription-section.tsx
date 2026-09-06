"use client";

/**
 * <ChildSubscriptionSection> — Story 6.4.
 *
 * "Abonnement de mon enfant" — free: CTA to Stripe Checkout (parent pays,
 * child benefits). Premium: status + "Mes abonnements" (next billing date,
 * cancel). §2 scope decision: no Stripe invoice-history list here — no
 * such integration exists anywhere in this codebase yet (see
 * `apps.family.services.parent_billing`'s own docstring).
 *
 * Fetches on mount (not passed from the server-fetched dashboard) — status
 * can change right after a Stripe redirect, and this keeps the already
 * Server-Component dashboard page simple.
 */
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  cancelChildSubscription,
  createChildCheckoutSession,
  fetchChildSubscriptionStatus,
  type ChildSubscriptionStatus,
} from "@/lib/api/parent";

export function ChildSubscriptionSection({ studentId }: { studentId: string }) {
  const [status, setStatus] = useState<ChildSubscriptionStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchChildSubscriptionStatus(studentId)
      .then((s) => {
        if (!cancelled) setStatus(s);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [studentId]);

  async function handleUpgrade() {
    setBusy(true);
    setErrorMessage(null);
    try {
      const { checkout_url } = await createChildCheckoutSession(studentId);
      window.location.href = checkout_url;
    } catch (err) {
      setBusy(false);
      setErrorMessage(
        err instanceof ApiError ? err.message : "Une erreur est survenue. Réessaie plus tard.",
      );
    }
  }

  async function handleCancel() {
    setBusy(true);
    setErrorMessage(null);
    try {
      const next = await cancelChildSubscription(studentId);
      setStatus(next);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : "Une erreur est survenue. Réessaie plus tard.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (!status) return null;

  return (
    <section
      aria-labelledby="child-subscription-title"
      className="rounded-lg border border-border bg-card p-4"
    >
      <h2 id="child-subscription-title" className="mb-2 text-h3 font-semibold text-text">
        Abonnement de mon enfant
      </h2>

      {errorMessage ? (
        <p role="alert" className="mb-2 text-danger">
          {errorMessage}
        </p>
      ) : null}

      {!status.is_premium ? (
        <div>
          <p className="mb-3 text-body-sm text-text-muted">
            Débloque pour ton enfant : l&apos;envoi anticipé de profil aux écoles partenaires, un
            suivi détaillé de ses parcours, et bien plus.
          </p>
          <Button onClick={handleUpgrade} disabled={busy}>
            {busy ? "Redirection…" : "Passer mon enfant en premium — 10,99 €/mois"}
          </Button>
        </div>
      ) : (
        <div>
          <p className="text-body-sm text-text">
            Premium actif{status.paid_by_parent ? " (payé par toi)" : ""}.
          </p>
          {status.current_period_end ? (
            <p className="text-body-sm text-text-muted">
              {status.cancel_at_period_end ? "Se termine le " : "Prochaine échéance : "}
              {new Date(status.current_period_end).toLocaleDateString("fr-FR", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </p>
          ) : null}
          {!status.cancel_at_period_end ? (
            <Button variant="outline" className="mt-3" onClick={handleCancel} disabled={busy}>
              {busy ? "Annulation…" : "Annuler l'abonnement"}
            </Button>
          ) : (
            <p className="mt-3 text-caption text-text-subtle">
              Annulation programmée — premium actif jusqu&apos;à la fin de la période payée.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
