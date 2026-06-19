"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  isBannerVisible,
  useDismissBulletinsBanner,
  useStudentProfile,
} from "@/hooks/use-student-profile";

interface BulletinsPostponedBannerProps {
  position?: "footer-fixed" | "sidebar";
  onAddClick: () => void;
}

export function BulletinsPostponedBanner({
  position = "footer-fixed",
  onAddClick,
}: BulletinsPostponedBannerProps) {
  const { data: profile, isLoading } = useStudentProfile();
  const dismiss = useDismissBulletinsBanner();

  if (isLoading || !profile || !isBannerVisible(profile)) {
    return null;
  }

  const isSidebar = position === "sidebar";

  return (
    <aside
      role="complementary"
      aria-label="Suggestion d'ajout bulletins"
      aria-live="polite"
      className={
        isSidebar
          ? "max-w-[320px] border border-border rounded-md bg-bg-2 p-3"
          : "fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-bg-2 px-4 py-3 flex items-center justify-between gap-3 max-h-14"
      }
    >
      <p className="text-sm text-muted-foreground flex-1">
        Tu peux ajouter tes bulletins à tout moment pour des stats
        personnalisées.
      </p>
      <div className="flex items-center gap-2 shrink-0">
        <Button variant="ghost" size="sm" onClick={onAddClick}>
          Ajouter →
        </Button>
        <button
          type="button"
          aria-label="Masquer ce bandeau"
          onClick={() => dismiss.mutate(undefined)}
          className="text-muted-foreground hover:text-foreground"
        >
          <X size={16} aria-hidden="true" />
          <span className="sr-only">Masquer pour 7 jours</span>
        </button>
      </div>
    </aside>
  );
}
