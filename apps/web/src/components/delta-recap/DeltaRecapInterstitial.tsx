"use client";

/**
 * `DeltaRecapInterstitial` — Story 8.6, UX-DR14 + UX-DR29.
 *
 * Full-screen interstitial shown ABOVE the `/accueil` dashboard when the
 * student returns at J+1+ with deltas (cards come pre-fetched from the
 * server component — no client fetch, no pop-in). "Tout vu, continuer"
 * unmounts it and reveals the home underneath (8.8's contract). Stable
 * state = the server passes zero cards and this renders nothing at all
 * (the AC's "redirection silencieuse": the home is already there).
 *
 * ALL sentences come from the backend (calm-tone linted in Python) — this
 * component renders strings and lays them out, it never writes copy. The
 * only local strings are chrome (heading, continue button, stat aria) in
 * `messages/fr.json#deltaRecap` (7.7 conventions).
 *
 * Dialog semantics (revue Epic 8, P0-4 — APG modal contract):
 * - Tab/Shift+Tab are TRAPPED inside the dialog (aria-modal alone only
 *   hides the page from assistive tech; sighted keyboard users could tab
 *   into invisible content behind the opaque overlay).
 * - body scroll is locked while open.
 * - On close, focus lands on the revealed page's h1 (`#accueil-title`).
 * - The heading is an h2: the page below keeps the single h1 of the view
 *   (double-h1 outline was the review's F13).
 *
 * Two ways out, two meanings (revue, P3 — consigned):
 * - "Tout vu, continuer" and every card CTA ACK (seen = cursor moves).
 * - Escape only CLOSES — same semantics as closing the tab: unseen deltas
 *   are still news and re-propose next visit. A reflex Esc must not
 *   silently consume a month of updates.
 *
 * Émotionnel: no confetti, no emoji, one primary CTA per card (AC).
 */

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";

import { CalendarNotification } from "@/components/notifications/CalendarNotification";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { acknowledgeDeltaRecap, type DeltaRecapCard } from "@/lib/api/delta-recap";

function StatChip({ before, after, label }: { before: number; after: number; label: string }) {
  // sr-only text + aria-hidden visual (revue P1-8): the old aria-label sat
  // on a <p> — a role where naming is prohibited (ARIA 1.2), so screen
  // readers never voiced the one number the card exists for.
  return (
    <p className="text-sm text-text-muted">
      <span className="sr-only">{label}</span>
      <span aria-hidden="true">
        {before} % → {after} %
      </span>
    </p>
  );
}

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function DeltaRecapInterstitial({ cards }: { cards: DeltaRecapCard[] }) {
  const t = useTranslations("deltaRecap");
  const [dismissed, setDismissed] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const open = cards.length > 0 && !dismissed;

  // Focus in + body scroll lock while open; both restored on close/unmount.
  useEffect(() => {
    if (!open) return;
    dialogRef.current?.focus();
    // Plain reset on close: nothing else in the app sets body overflow, and
    // capturing the "previous" value telescopes wrong when two instances
    // ever overlap (each would restore the other's "hidden").
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  const ackAndForget = () => {
    // Fire-and-forget with keepalive: the cursor move must never block the
    // unmount or a navigation — but a silent failure loop (e.g. stale CSRF
    // cookie) would re-propose the same recap forever, so it is at least
    // observable (revue P3).
    void acknowledgeDeltaRecap().catch((error) => {
      console.warn("[delta-recap] ack failed — recap will re-propose next visit", error);
    });
  };

  const dismissWithAck = () => {
    ackAndForget();
    setDismissed(true);
    restoreFocusToPage();
  };

  const closeWithoutAck = () => {
    setDismissed(true);
    restoreFocusToPage();
  };

  const restoreFocusToPage = () => {
    // After the overlay unmounts, the keyboard user must land on the
    // revealed home, not on <body> (revue F13).
    requestAnimationFrame(() => {
      document.getElementById("accueil-title")?.focus();
    });
  };

  const trapTab = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      closeWithoutAck();
      return;
    }
    if (event.key !== "Tab" || !dialogRef.current) return;
    // No visibility filtering needed: the dialog is an opaque overlay whose
    // every focusable is rendered (and offsetParent is unreliable both in
    // JSDOM and under position:fixed).
    const focusables = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (!first || !last) return;
    const active = document.activeElement;
    if (event.shiftKey && (active === first || active === dialogRef.current)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="delta-recap-title"
      tabIndex={-1}
      className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-background px-4 py-10"
      onKeyDown={trapTab}
    >
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6">
        <header className="flex flex-col gap-1">
          <h2 id="delta-recap-title" className="text-h1 font-semibold text-text md:text-h1-desktop">
            {t("title")}
          </h2>
          <p className="text-body text-text-muted">{t("intro")}</p>
        </header>

        <ul className="flex flex-col gap-4" aria-label={t("cardsLabel")}>
          {cards.map((card, index) => (
            <li key={`${card.kind}-${index}`}>
              <Card>
                {/* Calendar cards delegate to the shared CalendarNotification
                    (Story 8.7) — the ONE React renderer for the "calendrier
                    sans urgence" pattern; other kinds keep the local layout. */}
                {card.kind === "parcoursup_milestone" ? (
                  <CardContent className="pt-6">
                    <CalendarNotification
                      jalon={card.title}
                      daysUntil={card.days_until ?? 0}
                      body={card.body}
                      recommendedActions={card.recommended_actions ?? []}
                      ctaLabel={card.cta_label}
                      ctaUrl={card.cta_url}
                      onCtaClick={ackAndForget}
                      headingLevel="h3"
                    />
                  </CardContent>
                ) : (
                  <>
                    <CardHeader>
                      <h3 className="text-xl font-semibold text-text">{card.title}</h3>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-3">
                      <p className="text-text-muted">{card.body}</p>
                      {/* typeof guard (revue P3): a future kind whose stat
                          fields are ABSENT (undefined ≠ null) must hide the
                          chip, never render "undefined % → undefined %". */}
                      {typeof card.stat_before === "number" &&
                      typeof card.stat_after === "number" ? (
                        <StatChip
                          before={card.stat_before}
                          after={card.stat_after}
                          label={t("statLabel", {
                            before: card.stat_before,
                            after: card.stat_after,
                          })}
                        />
                      ) : null}
                      <Link
                        href={card.cta_url}
                        onClick={ackAndForget}
                        className="inline-block w-fit rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                      >
                        {card.cta_label}
                      </Link>
                    </CardContent>
                  </>
                )}
              </Card>
            </li>
          ))}
        </ul>

        <div className="pb-4">
          <Button variant="outline" onClick={dismissWithAck}>
            {t("continue")}
          </Button>
        </div>
      </div>
    </div>
  );
}
