"use client";

/**
 * FavoriteButton — heart toggle to add/remove a school from "mes paris".
 *
 * Story 4.8: uses useFavoriteSchool for optimistic state management.
 *
 * aria-pressed is the correct ARIA pattern for toggle buttons: it communicates
 * the binary pressed/unpressed state to assistive technology without requiring
 * a role="switch". The aria-label changes with state to give screen-reader
 * users a meaningful description of the current action.
 */

import { useFavoriteSchool } from "@/hooks/use-favorite-school";
import { cn } from "@/lib/utils";

interface FavoriteButtonProps {
  schoolSlug: string;
  initialFavorited?: boolean;
  className?: string;
}

export function FavoriteButton({
  schoolSlug,
  initialFavorited = false,
  className,
}: FavoriteButtonProps) {
  const { favorited, toggle, isPending } = useFavoriteSchool(schoolSlug, initialFavorited);

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={isPending}
      aria-label={favorited ? "Retirer de mes paris" : "Ajouter a mes paris"}
      aria-pressed={favorited}
      className={cn(
        "rounded-full p-2 transition-colors",
        favorited
          ? "text-red-500 hover:text-red-600"
          : "text-muted-foreground hover:text-foreground",
        className,
      )}
    >
      {favorited ? "♥" : "♡"}
    </button>
  );
}
