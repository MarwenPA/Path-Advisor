/**
 * Stripe client-side helper — Story 5.1.
 *
 * MVP uses hosted Stripe Checkout: the backend creates the session and we
 * redirect the browser to Stripe's hosted page. No Stripe.js / Elements bundle
 * is loaded here (that would be a dynamic import for LCP, NFR-P3, if ever
 * needed). No card data is handled client-side (PCI SAQ-A).
 */

import { createCheckoutSession } from "@/lib/api/billing";

/**
 * Start the premium subscription flow: create a checkout session and redirect
 * the browser to Stripe's hosted checkout page.
 */
export async function redirectToPremiumCheckout(): Promise<void> {
  const { checkout_url } = await createCheckoutSession();
  window.location.assign(checkout_url);
}
