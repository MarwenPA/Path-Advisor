"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

import { FicheMetier } from "@/components/professions/FicheMetier";
import type { FicheMetierProps } from "@/components/professions/types";
import type { SignalContributif } from "@/lib/api/recommendations";

// Story 7.9 — the drawer (radix Dialog/Sheet + BulletinsAddSheet) only ever
// appears on a signal click; loading it lazily keeps its chunk out of the
// LCP critical path of the public /metiers/{slug} page (`ssr: false` is
// safe: closed drawer renders nothing server-side anyway).
const SignauxDrawer = dynamic(
  () => import("@/components/professions/SignauxDrawer").then((m) => m.SignauxDrawer),
  { ssr: false },
);

interface FicheMetierClientProps extends Omit<FicheMetierProps, "onSignalClick"> {
  signalsContributifs: SignalContributif[];
  /**
   * Raw API confidence level ("low"|"medium"|"high") used directly by SignauxDrawer.
   * Only present when the user arrived via MetiersList query params — undefined on direct
   * URL access (shared link, refresh, SEO). In that case SignauxDrawer skips the
   * incomplete-profile context block (acceptable limitation for MVP).
   */
  drawerConfidenceLevel?: "low" | "medium" | "high";
}

export function FicheMetierClient({
  signalsContributifs,
  drawerConfidenceLevel,
  ...ficheProps
}: FicheMetierClientProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerSignals, setDrawerSignals] = useState<SignalContributif[]>([]);

  function handleSignalClick(signalId: string) {
    const found = signalsContributifs.filter((s) => s.signal === signalId);
    setDrawerSignals(found.length ? found : signalsContributifs);
    setDrawerOpen(true);
  }

  return (
    <>
      <FicheMetier {...ficheProps} onSignalClick={handleSignalClick} />
      <SignauxDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        metiersName={ficheProps.profession.name}
        signals={drawerSignals}
        confidenceLevel={drawerConfidenceLevel}
      />
    </>
  );
}
