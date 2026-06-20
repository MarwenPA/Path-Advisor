"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface TocSection {
  readonly key: string;
  readonly label: string;
}

interface FicheMetierTOCProps {
  sections: readonly TocSection[];
  activeSection: string;
  onSectionClick: (key: string) => void;
}

export function FicheMetierTOC({
  sections,
  activeSection,
  onSectionClick,
}: FicheMetierTOCProps) {
  return (
    <nav
      aria-label="Sections de la fiche"
      className="sticky top-20 self-start"
      style={{ width: "200px" }}
    >
      <ul className="flex flex-col gap-1">
        {sections.map((section) => {
          const isActive = activeSection === section.key;
          return (
            <li key={section.key}>
              <a
                href={`#section-${section.key}`}
                onClick={(e) => {
                  e.preventDefault();
                  onSectionClick(section.key);
                }}
                aria-current={isActive ? "true" : undefined}
                className={cn(
                  "block rounded px-2 py-1.5 text-body-sm",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "transition-colors duration-instant",
                  isActive
                    ? "bg-brand/10 font-semibold text-brand"
                    : "text-text-muted hover:text-text",
                )}
              >
                {section.label}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
