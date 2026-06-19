"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const STEPS = [
  { label: "Étape 1", path: "/onboarding/step-1" },
  { label: "Étape 2", path: "/onboarding/step-2" },
  { label: "Étape 3", path: "/onboarding/step-3" },
];

function getStepIndex(pathname: string): number {
  return STEPS.findIndex((s) => pathname.startsWith(s.path));
}

function getBackHref(stepIndex: number): string {
  if (stepIndex <= 0) return "/dashboard";
  return STEPS[stepIndex - 1].path;
}

export default function OnboardingLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const stepIndex = getStepIndex(pathname);
  const isOnboarding = stepIndex >= 0;

  if (!isOnboarding) return <>{children}</>;

  const backHref = getBackHref(stepIndex);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 pt-4 pb-2 max-w-lg mx-auto w-full">
        <Link
          href={backHref}
          aria-label="Retour"
          className={cn(
            "p-2 rounded-md text-[var(--color-text-muted)]",
            "hover:text-[var(--color-text)] hover:bg-[var(--color-bg-subtle)]",
            "focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]",
            "min-h-[44px] min-w-[44px] flex items-center justify-center"
          )}
        >
          <ChevronLeft className="size-5" aria-hidden />
        </Link>

        {/* Progress dots */}
        <nav aria-label="Progression de l'onboarding" className="flex items-center gap-2">
          {STEPS.map((step, i) => (
            <span
              key={step.path}
              aria-label={`${step.label}${i === stepIndex ? " (en cours)" : i < stepIndex ? " (terminée)" : ""}`}
              className={cn(
                "rounded-full transition-all",
                i === stepIndex
                  ? "w-5 h-2 bg-[var(--color-brand)]"
                  : i < stepIndex
                  ? "w-2 h-2 bg-[var(--color-brand)] opacity-60"
                  : "w-2 h-2 bg-[var(--color-border)]"
              )}
            />
          ))}
        </nav>

        {/* Spacer to balance the back button */}
        <div className="min-h-[44px] min-w-[44px]" aria-hidden />
      </header>

      <main className="flex-1">{children}</main>
    </div>
  );
}
