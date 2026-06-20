"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";

import { cn } from "@/lib/utils";

/**
 * Lightweight CSS/ARIA tooltip — no `@radix-ui/react-tooltip` dependency.
 *
 * Compound API (shadcn-shaped):
 *
 *   <Tooltip>
 *     <TooltipTrigger asChild><button>…</button></TooltipTrigger>
 *     <TooltipContent>Full text</TooltipContent>
 *   </Tooltip>
 *
 * The trigger and content share an id via context: the trigger gets
 * `aria-describedby` so screen readers announce the content, and the bubble
 * appears on hover (CSS group-hover) and keyboard focus (group-focus-within).
 * The bubble stays in the DOM (referenced by id) so AT can read it on demand.
 */

interface TooltipContextValue {
  id: string;
}

const TooltipContext = React.createContext<TooltipContextValue | null>(null);

function useTooltipContext(component: string): TooltipContextValue {
  const ctx = React.useContext(TooltipContext);
  if (!ctx) {
    throw new Error(`${component} must be used within <Tooltip>`);
  }
  return ctx;
}

interface TooltipProps {
  children: React.ReactNode;
  className?: string;
}

export function Tooltip({ children, className }: TooltipProps) {
  const reactId = React.useId();
  const id = `tooltip-${reactId}`;
  return (
    <TooltipContext.Provider value={{ id }}>
      <span className={cn("group relative inline-flex", className)}>{children}</span>
    </TooltipContext.Provider>
  );
}

interface TooltipTriggerProps extends React.HTMLAttributes<HTMLElement> {
  /** Render the single child as the trigger instead of wrapping in a <span>. */
  asChild?: boolean;
  children: React.ReactNode;
}

export function TooltipTrigger({ asChild = false, children, ...props }: TooltipTriggerProps) {
  const { id } = useTooltipContext("TooltipTrigger");
  const Comp = asChild ? Slot : "span";
  return (
    <Comp aria-describedby={id} {...props}>
      {children}
    </Comp>
  );
}

interface TooltipContentProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
}

export function TooltipContent({ children, className, ...props }: TooltipContentProps) {
  const { id } = useTooltipContext("TooltipContent");
  return (
    <span
      id={id}
      role="tooltip"
      className={cn(
        "pointer-events-none absolute bottom-full left-1/2 z-20 mb-1 -translate-x-1/2",
        "w-max max-w-xs rounded-md border border-border bg-card px-2.5 py-1.5",
        "text-caption text-text shadow-sm",
        "opacity-0 transition-opacity duration-instant",
        "group-hover:opacity-100 group-focus-within:opacity-100",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
