"use client";

/**
 * <PaywallContextuel> — Story 5.11.
 *
 * Generic component shown when a free user attempts a premium feature.
 * Renders as a bottom Sheet (mirrors the `<SendOutreachButton>`/
 * `<EcoleRespondForm>` Sheet pattern already used elsewhere): contextual
 * title, 1-2 sentence description, 2-3 benefits, primary CTA "Passer en
 * premium — 10,99 €/mois" (links to `/premium`, where the real Stripe
 * checkout via `<PremiumCheckoutButton>` already lives — no checkout
 * logic duplicated here), secondary CTA "Plus tard".
 *
 * Emotional-compliance AC (anti-urgence, anti-FOMO): no countdown, no
 * "tu rates des opportunités" framing — `description`/`benefits` are
 * plain factual copy, supplied by the caller.
 *
 * Cooldown (AC): once dismissed via "Plus tard", the trigger stops
 * re-opening the Sheet for the rest of the session (per `feature` key) —
 * a further tap goes straight to `/premium` instead of re-showing the
 * same pitch. sessionStorage (not localStorage): a new browser session
 * sees the paywall again, matching the spec's own anti-pattern list.
 */
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";

export interface PaywallContextuelProps {
  /** Cooldown key — one per distinct premium feature (e.g. "envoi-anticipe"). */
  feature: string;
  /** Contextual title, e.g. "Envoyer ton profil aux écoles est une feature premium". */
  title: string;
  /** 1-2 factual sentences — what this feature does, not what the user is missing. */
  description: string;
  /** 2-3 concrete benefits, plain statements. */
  benefits: string[];
  /** The element that opens the paywall on click. */
  children: React.ReactNode;
}

function seenThisSession(feature: string): boolean {
  try {
    return sessionStorage.getItem(`paywall_seen_${feature}`) === "1";
  } catch {
    return false;
  }
}

function markSeen(feature: string): void {
  try {
    sessionStorage.setItem(`paywall_seen_${feature}`, "1");
  } catch {
    // sessionStorage unavailable (private mode, SSR) — cooldown just won't persist.
  }
}

export function PaywallContextuel({
  feature,
  title,
  description,
  benefits,
  children,
}: PaywallContextuelProps) {
  const [open, setOpen] = useState(false);

  function handleTriggerClick() {
    if (seenThisSession(feature)) {
      window.location.href = "/premium";
      return;
    }
    setOpen(true);
  }

  function handleLater() {
    markSeen(feature);
    setOpen(false);
  }

  return (
    <>
      <span onClick={handleTriggerClick} role="button" tabIndex={0}>
        {children}
      </span>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="bottom">
          <SheetHeader>
            <SheetTitle>{title}</SheetTitle>
          </SheetHeader>
          <div className="flex flex-col gap-3 py-4 text-body-sm text-text">
            <p>{description}</p>
            <ul className="list-disc pl-5">
              {benefits.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
          <SheetFooter className="gap-2">
            <Button variant="outline" onClick={handleLater}>
              Plus tard
            </Button>
            <Button asChild>
              <Link href="/premium">Passer en premium — 10,99 €/mois</Link>
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </>
  );
}
