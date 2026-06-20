"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { ScoreVocationnel } from "@/components/professions/ScoreVocationnel";
import { SignauxDrawer } from "@/components/professions/SignauxDrawer";
import type { Signal } from "@/components/professions/types";
import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import type { ScoredProfession } from "@/lib/api/recommendations";

const FIRST_VISIT_KEY = "recos_seen_v1";
const STAGGER_MS = 100;

/** Map ai-service confidence_level to ScoreVocationnel confidenceLevel prop. */
function mapConfidence(level: "low" | "medium" | "high"): "normal" | "indicative" {
  return level === "low" ? "indicative" : "normal";
}

/** Extract top-2 signal chips from signals_contributifs. */
function toSignals(profession: ScoredProfession): Signal[] {
  return profession.signals_contributifs.slice(0, 2).map((s) => ({
    id: s.signal,
    label: s.signal.replace(/_/g, " "),
  }));
}

interface MetiersListProps {
  professions: ScoredProfession[];
}

export function MetiersList({ professions }: MetiersListProps) {
  const reducedMotion = usePrefersReducedMotion();

  const skipAnimation =
    reducedMotion ||
    (typeof window !== "undefined" && localStorage.getItem(FIRST_VISIT_KEY) === "1");

  const [visibleCount, setVisibleCount] = useState(skipAnimation ? professions.length : 0);
  const animationStarted = useRef(false);

  // Drawer state — which profession's signals to show
  const [drawerProfession, setDrawerProfession] = useState<ScoredProfession | null>(null);

  useEffect(() => {
    if (skipAnimation) return;
    if (animationStarted.current) return;
    animationStarted.current = true;

    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setVisibleCount(i);
      if (i >= professions.length) {
        clearInterval(interval);
        localStorage.setItem(FIRST_VISIT_KEY, "1");
      }
    }, STAGGER_MS);

    return () => clearInterval(interval);
  }, [professions.length, skipAnimation]);

  if (professions.length === 0) {
    return (
      <p className="text-body text-gray-500">
        Aucune recommandation disponible pour le moment. Complète ton profil pour obtenir tes
        premières suggestions.
      </p>
    );
  }

  return (
    <>
      <ul className="flex flex-col gap-4" data-testid="metiers-list">
        {professions.map((p, idx) => {
          const visible = idx < visibleCount;
          const encodedSignals = encodeURIComponent(JSON.stringify(p.signals_contributifs));
          return (
            <li
              key={p.id}
              className="transition-all duration-500"
              style={{
                opacity: visible ? 1 : 0,
                transform: visible ? "translateY(0)" : "translateY(12px)",
              }}
              aria-hidden={!visible}
            >
              <Link
                href={`/metiers/${p.slug}?score=${p.score}&confidence=${p.confidence_level}&signals=${encodedSignals}`}
                className="block rounded-xl border border-gray-200 p-4 hover:border-blue-400 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                <ScoreVocationnel
                  metierId={p.id}
                  metiersName={p.name}
                  score={p.score}
                  phraseRecopiable={p.phrase_recopiable}
                  signals={toSignals(p)}
                  variant="compact"
                  confidenceLevel={mapConfidence(p.confidence_level)}
                  onSignalClick={() => {
                    setDrawerProfession(p);
                  }}
                />
              </Link>
            </li>
          );
        })}
      </ul>

      <SignauxDrawer
        open={drawerProfession !== null}
        onOpenChange={(open) => {
          if (!open) setDrawerProfession(null);
        }}
        metiersName={drawerProfession?.name ?? ""}
        signals={drawerProfession?.signals_contributifs ?? []}
      />
    </>
  );
}
