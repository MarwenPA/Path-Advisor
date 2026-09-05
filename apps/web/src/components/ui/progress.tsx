import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * `<Progress>` — minimal determinate progress bar.
 *
 * Code-review fix (2026-09): `upload-progress.tsx` (Story 2.3 bulletin
 * upload) has imported this from `@/components/ui/progress` since it was
 * written, but the component was never created — every build hit
 * `/onboarding/step-3` and 500'd on "Continuer avec les bulletins".
 *
 * No `@radix-ui/react-progress` dependency (not in the repo, same call as
 * `account-menu.tsx`'s popover — a determinate 0-100 bar doesn't need it):
 * a `role="progressbar"` div with an inner indicator whose width tracks
 * `value`. Callers pass their own `aria-valuenow`/`aria-valuemin`/
 * `aria-valuemax`/`aria-label` (see `upload-progress.tsx`) — spread through
 * via `...props`, not duplicated here.
 */
export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 0-100. Values outside that range are clamped. */
  value: number;
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ value, className, ...props }, ref) => {
    const clamped = Math.min(100, Math.max(0, value));
    return (
      <div
        ref={ref}
        role="progressbar"
        className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)}
        {...props}
      >
        <div
          className="h-full rounded-full bg-brand transition-[width] duration-300 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
    );
  },
);
Progress.displayName = "Progress";
