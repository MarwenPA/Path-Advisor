"use client";

import { useState } from "react";

import { FicheMetier } from "@/components/professions/FicheMetier";
import { SignauxDrawer } from "@/components/professions/SignauxDrawer";
import type { FicheMetierProps } from "@/components/professions/types";
import type { SignalContributif } from "@/lib/api/recommendations";

interface FicheMetierClientProps extends Omit<FicheMetierProps, "onSignalClick"> {
  signalsContributifs: SignalContributif[];
}

export function FicheMetierClient({ signalsContributifs, ...ficheProps }: FicheMetierClientProps) {
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
      />
    </>
  );
}
