/**
 * API fetchers for billing / premium subscription — Story 5.1.
 *
 * `createCheckoutSession` asks the backend to create a hosted Stripe Checkout
 * session and returns its URL; the caller redirects the browser to it (see
 * `@/lib/stripe/client`). No card data is ever handled client-side (PCI SAQ-A).
 * All JSON field names stay snake_case (project-wide convention).
 */

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export async function createCheckoutSession(): Promise<CheckoutSessionResponse> {
  return apiFetch<CheckoutSessionResponse>("/api/v1/billing/checkout-session", {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}
