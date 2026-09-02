"use client";

/**
 * <PremiumCheckoutButton> — Story 5.3 §T6/AC1.
 *
 * Client Component island: calls the existing `redirectToPremiumCheckout()`
 * (built in Story 5.1, unwired until now) and redirects the browser to
 * Stripe's hosted Checkout. No card data is ever handled here (PCI SAQ-A).
 */
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { redirectToPremiumCheckout } from "@/lib/stripe/client";
import { BILLING_COPY } from "@/lib/i18n/fr/billing";

const COPY = BILLING_COPY.premium;

export function PremiumCheckoutButton() {
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  const handleClick = async () => {
    setStatus("loading");
    try {
      await redirectToPremiumCheckout();
      // On success the browser navigates away — no further state update needed.
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <Button onClick={handleClick} disabled={status === "loading"}>
        {status === "loading" ? COPY.ctaLoading : COPY.ctaLabel}
      </Button>
      {status === "error" ? (
        <p className="text-text-error text-sm" role="alert">
          {COPY.errorMessage}
        </p>
      ) : null}
    </div>
  );
}
