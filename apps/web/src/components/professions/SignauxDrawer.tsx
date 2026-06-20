"use client";

import * as React from "react";
import { BookOpen, Heart, Star, Zap } from "lucide-react";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { SignalContributif } from "@/lib/api/recommendations";

// ─── Mobile detection ─────────────────────────────────────────────────────────

function useIsMobile() {
  return React.useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia("(max-width: 1023px)");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia("(max-width: 1023px)").matches,
    () => false,
  );
}

// ─── Signal helpers ───────────────────────────────────────────────────────────

type SignalCategory = "passion" | "valeur" | "spécialité" | "autre";

const CATEGORY_ICONS: Record<SignalCategory, React.ElementType> = {
  passion: Heart,
  valeur: Star,
  spécialité: BookOpen,
  autre: Zap,
};

function formatSignalLabel(signal: string): { category: SignalCategory; label: string } {
  const [cat, ...rest] = signal.split("_");
  const raw = rest.join(" ").replace(/-/g, " ");
  const label = raw.charAt(0).toUpperCase() + raw.slice(1);
  const categoryMap: Record<string, SignalCategory> = {
    passion: "passion",
    valeur: "valeur",
    specialite: "spécialité",
  };
  return { category: categoryMap[cat ?? ""] ?? "autre", label: label || signal };
}

// ─── Props ────────────────────────────────────────────────────────────────────

export interface SignauxDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  metiersName: string;
  signals: SignalContributif[];
}

// ─── Signal list content ──────────────────────────────────────────────────────

function SignauxContent({
  metiersName,
  signals,
}: Pick<SignauxDrawerProps, "metiersName" | "signals">) {
  const sorted = [...signals].sort((a, b) => b.contribution - a.contribution);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-body-sm text-text-muted">
        Voilà les ingrédients qui ont fait monter {metiersName}
      </p>

      {sorted.length === 0 ? (
        <p className="text-body text-text-muted">
          Les signaux détaillés ne sont pas disponibles pour ce métier
        </p>
      ) : (
        <ul className="flex flex-col gap-3" role="list">
          {sorted.map((s) => {
            const { category, label } = formatSignalLabel(s.signal);
            const Icon = CATEGORY_ICONS[category];
            return (
              <li
                key={s.signal}
                className="flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2"
                aria-label={`${category} ${label} : +${s.contribution} pts`}
              >
                <Icon size={16} className="shrink-0 text-text-muted" aria-hidden />
                <div className="flex flex-1 items-center justify-between gap-2">
                  <div className="flex flex-col">
                    <span className="text-caption font-medium uppercase tracking-wide text-text-muted">
                      {category}
                    </span>
                    <span className="text-body text-text">{label}</span>
                  </div>
                  <span className="font-mono text-body-sm font-semibold text-brand">
                    +{s.contribution}&nbsp;pts
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <div className="mt-2 flex flex-col gap-2 border-t border-border pt-4">
        <a
          href="/revue-humaine"
          className="text-body-sm text-brand underline-offset-2 hover:underline"
        >
          Demander une revue humaine
        </a>
        <a
          href="/methodologie"
          className="text-body-sm text-text-muted underline-offset-2 hover:underline"
        >
          Comment ça marche
        </a>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function SignauxDrawer({ open, onOpenChange, metiersName, signals }: SignauxDrawerProps) {
  const isMobile = useIsMobile();
  const title = "Pourquoi ce métier ?";

  const content = <SignauxContent metiersName={metiersName} signals={signals} />;

  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent
          side="bottom"
          className="max-h-[90dvh] overflow-y-auto rounded-t-xl px-6 py-6"
        >
          <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-border" aria-hidden />
          <SheetHeader className="mb-4">
            <SheetTitle>{title}</SheetTitle>
          </SheetHeader>
          {content}
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        {content}
      </DialogContent>
    </Dialog>
  );
}
