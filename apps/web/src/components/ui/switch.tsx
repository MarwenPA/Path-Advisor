"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Switch — Story 8.2 (no ui/ switch existed; `@radix-ui/react-switch` is not
 * a dependency, and a native input needs none).
 *
 * A styled native `<input type="checkbox" role="switch">`:
 *   - keyboard operable out of the box (Tab focuses, Space toggles);
 *   - labelable, so callers associate a real `<label htmlFor>` (RGAA);
 *   - state is exposed to AT via the native checked state.
 *
 * RGAA note (state not conveyed by colour alone): the thumb changes SIDE
 * (left = off, right = on), not just the track colour — and the
 * notifications settings page additionally pairs each switch with visible
 * "Activé / Désactivé" text.
 *
 * Revue Epic 8 (P2-8): the off-state track uses `control-off` (≈3.9:1 on
 * the page ground — WCAG 1.4.11 non-text contrast; bg-3 sat at ≈1.2:1, an
 * invisible control in sunlight). Callers must NOT `disabled` the input
 * during an in-flight save: disabling ejects keyboard focus to <body> —
 * gate in the change handler and set `aria-busy` instead.
 */
const Switch = React.forwardRef<
  HTMLInputElement,
  Omit<React.InputHTMLAttributes<HTMLInputElement>, "type">
>(({ className, ...props }, ref) => (
  <span className={cn("relative inline-flex h-6 w-11 shrink-0", className)}>
    <input
      ref={ref}
      type="checkbox"
      role="switch"
      className="peer h-full w-full cursor-pointer appearance-none rounded-full border border-control-off bg-control-off transition-colors checked:border-primary checked:bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 aria-busy:cursor-wait"
      {...props}
    />
    {/* Decorative thumb — slides right when the peer input is checked. */}
    <span
      aria-hidden
      className="pointer-events-none absolute left-1 top-1 h-4 w-4 rounded-full bg-background shadow transition-transform peer-checked:translate-x-5 peer-disabled:opacity-50"
    />
  </span>
));
Switch.displayName = "Switch";

export { Switch };
