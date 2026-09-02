/**
 * /premium — Story 5.3 §T6/AC1.
 *
 * Checkout entry point: plan/price/benefits + CTA. If the user is already
 * premium, shows a short message + link to manage the subscription instead
 * of a redundant checkout button.
 */
import Link from "next/link";

import { PremiumCheckoutButton } from "@/components/features/billing/premium-checkout-button";
import { getSubscription } from "@/lib/api/billing";
import { BILLING_COPY } from "@/lib/i18n/fr/billing";

export const dynamic = "force-dynamic";

export default async function PremiumPage() {
  const COPY = BILLING_COPY.premium;
  const subscription = await getSubscription();

  return (
    <main className="mx-auto w-full max-w-lg px-4 py-8">
      <h1 className="text-h1 font-bold text-text">{COPY.pageTitle}</h1>
      <p className="mt-2 text-h2 font-semibold text-text">{COPY.price}</p>
      <p className="mt-1 text-body text-text-muted">{COPY.tagline}</p>

      <ul className="mt-6 flex flex-col gap-2">
        {COPY.benefits.map((benefit) => (
          <li key={benefit} className="text-body text-text">
            • {benefit}
          </li>
        ))}
      </ul>

      <div className="mt-8">
        {subscription.is_premium ? (
          <div className="flex flex-col gap-2">
            <p className="text-body text-text-muted">{COPY.alreadyPremium}</p>
            <Link
              href="/parametres/abonnement"
              className="text-body-sm text-primary hover:underline"
            >
              {COPY.manageLink}
            </Link>
          </div>
        ) : (
          <PremiumCheckoutButton />
        )}
      </div>
    </main>
  );
}
