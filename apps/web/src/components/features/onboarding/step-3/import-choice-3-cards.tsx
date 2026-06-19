"use client";

import { ArrowRight, Camera, Pencil } from "lucide-react";

import { cn } from "@/lib/utils";

export type CardChoice = "scan" | "manual" | "later";

type Card = {
  id: CardChoice;
  icon: React.ReactNode;
  title: string;
  description: string;
  timing: string;
  ariaLabel: string;
};

const CARDS: Card[] = [
  {
    id: "scan",
    icon: <Camera className="size-6 text-[var(--color-text-muted)]" aria-hidden />,
    title: "Scanner / importer mes bulletins",
    description: "Photo ou PDF, on lit pour toi",
    timing: "~30 secondes",
    ariaLabel: "Scanner ou importer mes bulletins, environ 30 secondes",
  },
  {
    id: "manual",
    icon: <Pencil className="size-6 text-[var(--color-text-muted)]" aria-hidden />,
    title: "Saisir mes notes à la main",
    description: "Formulaire structuré, simple",
    timing: "~3 minutes",
    ariaLabel: "Saisir mes notes à la main, environ 3 minutes",
  },
  {
    id: "later",
    icon: <ArrowRight className="size-6 text-[var(--color-text-muted)]" aria-hidden />,
    title: "Plus tard, je préfère explorer d'abord",
    description: "Tu pourras ajouter à tout moment",
    timing: "Recos un peu plus génériques pour l'instant",
    ariaLabel:
      "Plus tard, je préfère explorer d'abord. Tu pourras ajouter tes bulletins à tout moment",
  },
];

type Props = {
  onSelect: (choice: CardChoice) => void;
  className?: string;
};

export function ImportChoice3Cards({ onSelect, className }: Props) {
  return (
    <nav aria-label="Options d'import bulletins" className={cn("flex flex-col gap-4", className)}>
      <ul className="flex flex-col gap-4 list-none p-0 m-0">
        {CARDS.map((card) => (
          <li key={card.id}>
            <button
              type="button"
              aria-label={card.ariaLabel}
              onClick={() => onSelect(card.id)}
              className={cn(
                // Identical visual treatment for all 3 cards — no ribbon, no color distinction (AC1)
                "w-full text-left rounded-[var(--radius-lg)] border border-[var(--color-border)]",
                "bg-[var(--color-bg-2)] p-6 min-h-[80px]",
                "flex items-start gap-4",
                "focus-visible:outline-2 focus-visible:outline-[var(--color-brand)] focus-visible:outline-offset-2",
                "hover:bg-[var(--color-bg-3)] transition-colors duration-150",
                "cursor-pointer"
              )}
            >
              <span className="mt-0.5 shrink-0">{card.icon}</span>
              <span className="flex flex-col gap-1">
                <span className="text-[var(--text-h3)] font-semibold text-[var(--color-text)]">
                  {card.title}
                </span>
                <span className="text-[var(--text-body)] text-[var(--color-text-muted)]">
                  {card.description}
                </span>
                <span className="text-[var(--text-caption)] text-[var(--color-text-subtle)]">
                  {card.timing}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
