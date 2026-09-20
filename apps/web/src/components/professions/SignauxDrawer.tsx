"use client";

import * as React from "react";
import Link from "next/link";
import { BookOpen, Heart, Star, Zap } from "lucide-react";
import { useTranslations } from "next-intl";

import { BulletinsAddSheet } from "@/components/features/bulletins/bulletins-add-sheet";
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

// Internal discriminant (icon lookup + catalog key) — the displayed category
// name lives in the catalog under `ficheMetier.signauxDrawer.categories.*`.
type SignalCategory = "passion" | "valeur" | "specialite" | "autre";

const CATEGORY_ICONS: Record<SignalCategory, React.ElementType> = {
  passion: Heart,
  valeur: Star,
  specialite: BookOpen,
  autre: Zap,
};

function formatSignalLabel(signal: string): { category: SignalCategory; label: string } {
  const [cat, ...rest] = signal.split("_");
  const raw = rest.join(" ").replace(/-/g, " ");
  const label = raw.charAt(0).toUpperCase() + raw.slice(1);
  const categoryMap: Record<string, SignalCategory> = {
    passion: "passion",
    valeur: "valeur",
    specialite: "specialite",
  };
  return { category: categoryMap[cat ?? ""] ?? "autre", label: label || signal };
}

// ─── Props ────────────────────────────────────────────────────────────────────

export interface SignauxDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  metiersName: string;
  signals: SignalContributif[];
  /** Story 3.10: show factual context + bulletin CTA when score is indicative. */
  confidenceLevel?: "low" | "medium" | "high";
}

// ─── Signal list content ──────────────────────────────────────────────────────

// ─── Incomplete-profile context block (Story 3.10, AC2) ──────────────────────

interface IncompleteProfileContextProps {
  onAddBulletins: () => void;
}

function IncompleteProfileContext({ onAddBulletins }: IncompleteProfileContextProps) {
  const t = useTranslations("ficheMetier.signauxDrawer");
  return (
    <aside
      aria-label={t("incompleteAria")}
      className="rounded-lg border border-border bg-bg-2 px-4 py-3 text-body-sm text-text-muted"
      data-testid="incomplete-profile-context"
    >
      <p>{t("incompleteBody")}</p>
      <button
        type="button"
        onClick={onAddBulletins}
        className="mt-2 text-brand underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {t("incompleteCta")}
      </button>
    </aside>
  );
}

// ─── Signal list content ──────────────────────────────────────────────────────

function SignauxContent({
  metiersName,
  signals,
  confidenceLevel,
  onAddBulletins,
}: Pick<SignauxDrawerProps, "metiersName" | "signals" | "confidenceLevel"> & {
  onAddBulletins: () => void;
}) {
  const t = useTranslations("ficheMetier.signauxDrawer");
  const sorted = [...signals].sort((a, b) => b.contribution - a.contribution);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-body-sm text-text-muted">{t("intro", { name: metiersName })}</p>

      {sorted.length === 0 ? (
        <p className="text-body text-text-muted">{t("empty")}</p>
      ) : (
        <ul className="flex flex-col gap-3" role="list">
          {sorted.map((s) => {
            const { category, label } = formatSignalLabel(s.signal);
            const categoryLabel = t(`categories.${category}`);
            const Icon = CATEGORY_ICONS[category];
            return (
              <li
                key={s.signal}
                className="flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2"
                aria-label={t("itemAria", {
                  category: categoryLabel,
                  label,
                  points: s.contribution,
                })}
              >
                <Icon size={16} className="shrink-0 text-text-muted" aria-hidden />
                <div className="flex flex-1 items-center justify-between gap-2">
                  <div className="flex flex-col">
                    <span className="text-caption font-medium uppercase tracking-wide text-text-muted">
                      {categoryLabel}
                    </span>
                    <span className="text-body text-text">{label}</span>
                  </div>
                  <span className="font-mono text-body-sm font-semibold text-brand">
                    {t("points", { points: s.contribution })}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {confidenceLevel === "low" && <IncompleteProfileContext onAddBulletins={onAddBulletins} />}

      <div className="mt-2 flex flex-col gap-2 border-t border-border pt-4">
        <Link
          href="/revue-humaine"
          className="text-body-sm text-brand underline-offset-2 hover:underline"
        >
          {t("reviewLink")}
        </Link>
        <Link
          href="/methodologie"
          className="text-body-sm text-text-muted underline-offset-2 hover:underline"
        >
          {t("methodologyLink")}
        </Link>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function SignauxDrawer({
  open,
  onOpenChange,
  metiersName,
  signals,
  confidenceLevel,
}: SignauxDrawerProps) {
  const t = useTranslations("ficheMetier.signauxDrawer");
  const isMobile = useIsMobile();
  const [bulletinsSheetOpen, setBulletinsSheetOpen] = React.useState(false);
  const title = t("title");

  const content = (
    <SignauxContent
      metiersName={metiersName}
      signals={signals}
      confidenceLevel={confidenceLevel}
      onAddBulletins={() => setBulletinsSheetOpen(true)}
    />
  );

  const bulletinsSheet = (
    <BulletinsAddSheet
      open={bulletinsSheetOpen}
      onClose={() => setBulletinsSheetOpen(false)}
      onSuccess={() => setBulletinsSheetOpen(false)}
    />
  );

  if (isMobile) {
    return (
      <>
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
        {bulletinsSheet}
      </>
    );
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
          </DialogHeader>
          {content}
        </DialogContent>
      </Dialog>
      {bulletinsSheet}
    </>
  );
}
