/**
 * /parametres/abonnement — Story 5.3 §T8/AC3.
 *
 * Shows tier/status/period + lets a premium user cancel (scheduled at period
 * end) via `ConsentDialog`. A free user sees an upgrade CTA to `/premium`.
 */
import Link from "next/link";

import { CancelSubscriptionButton } from "@/components/features/billing/cancel-subscription-button";
import { getSubscription } from "@/lib/api/billing";
import { BILLING_COPY } from "@/lib/i18n/fr/billing";

export const dynamic = "force-dynamic";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

const STATUS_LABELS: Record<string, string> = {
  active: BILLING_COPY.settings.statusActive,
  past_due: BILLING_COPY.settings.statusPastDue,
  cancelled: BILLING_COPY.settings.statusCancelled,
};

export default async function AbonnementPage() {
  const COPY = BILLING_COPY.settings;
  const subscription = await getSubscription();
  const tierLabel = subscription.tier === "premium" ? COPY.tierPremium : COPY.tierFree;
  const statusLabel = STATUS_LABELS[subscription.status] ?? subscription.status;

  return (
    <main className="mx-auto w-full max-w-lg px-4 py-8">
      <h1 className="text-h1 font-bold text-text">{COPY.title}</h1>

      <div className="mt-6 rounded-lg border border-border bg-card p-4">
        <p className="text-body font-medium text-text">{tierLabel}</p>
        {subscription.tier === "premium" && (
          <>
            <p className="mt-1 text-body-sm text-text-muted">{statusLabel}</p>
            {subscription.cancel_at_period_end ? (
              <p className="mt-2 text-body-sm text-text-subtle">
                {COPY.endsOn(formatDate(subscription.current_period_end))}
              </p>
            ) : (
              subscription.current_period_end && (
                <p className="mt-2 text-body-sm text-text-subtle">
                  {COPY.renewsOn(formatDate(subscription.current_period_end))}
                </p>
              )
            )}
          </>
        )}
      </div>

      <div className="mt-6">
        {subscription.tier !== "premium" ? (
          <Link
            href="/premium"
            className="inline-block rounded-md bg-primary px-4 py-2 text-body-sm font-medium text-primary-foreground hover:opacity-90"
          >
            {COPY.upgradeCta}
          </Link>
        ) : subscription.cancel_at_period_end ? (
          <p className="text-body-sm text-text-muted">{COPY.alreadyScheduled}</p>
        ) : (
          <CancelSubscriptionButton />
        )}
      </div>
    </main>
  );
}
