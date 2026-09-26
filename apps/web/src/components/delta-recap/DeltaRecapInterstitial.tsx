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
 * Every card CTA also acks (fire-and-forget) before navigating: going
 * through a card = having seen the recap. Closing the tab without acking
 * re-proposes the same deltas next visit (backend cursor semantics).
 *
 * Émotionnel: no confetti, no emoji, one primary CTA per card (AC).
 */

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { acknowledgeDeltaRecap, type DeltaRecapCard } from "@/lib/api/delta-recap";

function StatChip({ before, after, label }: { before: number; after: number; label: string }) {
  return (
    <p className="text-sm text-muted-foreground" aria-label={label}>
      <span aria-hidden="true">
        {before} % → {after} %
      </span>
    </p>
  );
}

export function DeltaRecapInterstitial({ cards }: { cards: DeltaRecapCard[] }) {
  const t = useTranslations("deltaRecap");
  const [dismissed, setDismissed] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Move focus into the dialog on open (RGAA: the interstitial takes over
  // the page; keyboard users must land inside it, not behind it).
  useEffect(() => {
    if (cards.length > 0 && !dismissed) dialogRef.current?.focus();
  }, [cards.length, dismissed]);

  if (cards.length === 0 || dismissed) return null;

  const dismiss = () => {
    // Fire-and-forget: the cursor move must never block the unmount (a
    // failed ack only means the recap shows again next visit — harmless).
    void acknowledgeDeltaRecap().catch(() => undefined);
    setDismissed(true);
  };

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="delta-recap-title"
      tabIndex={-1}
      className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-background px-4 py-10"
      onKeyDown={(event) => {
        if (event.key === "Escape") dismiss();
      }}
    >
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6">
        <header className="flex flex-col gap-1">
          <h1 id="delta-recap-title" className="text-h1 font-semibold text-text">
            {t("title")}
          </h1>
          <p className="text-body text-text-muted">{t("intro")}</p>
        </header>

        <ul className="flex flex-col gap-4" aria-label={t("cardsLabel")}>
          {cards.map((card, index) => (
            <li key={`${card.kind}-${index}`}>
              <Card>
                <CardHeader>
                  <h2 className="text-xl font-semibold text-foreground">{card.title}</h2>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <p className="text-muted-foreground">{card.body}</p>
                  {card.stat_before !== null && card.stat_after !== null ? (
                    <StatChip
                      before={card.stat_before}
                      after={card.stat_after}
                      label={t("statLabel", {
                        before: card.stat_before,
                        after: card.stat_after,
                      })}
                    />
                  ) : null}
                  {card.recommended_actions && card.recommended_actions.length > 0 ? (
                    <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                      {card.recommended_actions.map((action) => (
                        <li key={action}>{action}</li>
                      ))}
                    </ul>
                  ) : null}
                  <Link
                    href={card.cta_url}
                    onClick={() => void acknowledgeDeltaRecap().catch(() => undefined)}
                    className="inline-block w-fit rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    {card.cta_label}
                  </Link>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>

        <div className="pb-4">
          <Button variant="outline" onClick={dismiss}>
            {t("continue")}
          </Button>
        </div>
      </div>
    </div>
  );
}
