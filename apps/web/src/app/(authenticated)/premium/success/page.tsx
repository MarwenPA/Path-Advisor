/**
 * /premium/success — Story 5.3 §T7/AC2.
 *
 * Stripe's `success_url` (STRIPE_CHECKOUT_SUCCESS_URL) lands here after a
 * completed Checkout. Deliberately does NOT poll `getSubscription()` here —
 * the webhook (5.2) can land a few hundred ms after the redirect, so
 * `is_premium` could briefly still read `false` and flash a wrong "not
 * premium yet" state. The confirmation email (also triggered by the webhook)
 * is the durable proof; this page just closes the loop visually.
 */
import Link from "next/link";

import { BILLING_COPY } from "@/lib/i18n/fr/billing";

export const dynamic = "force-dynamic";

export default function PremiumSuccessPage() {
  const COPY = BILLING_COPY.success;

  return (
    <main className="mx-auto w-full max-w-lg px-4 py-8 text-center">
      <h1 className="text-h1 font-bold text-text">{COPY.pageTitle}</h1>
      <p className="mt-4 text-body text-text-muted">{COPY.message}</p>
      <Link href="/" className="mt-8 inline-block text-body-sm text-primary hover:underline">
        {COPY.ctaLabel}
      </Link>
    </main>
  );
}
