import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * `<Textarea>` — shadcn-style autosizing-friendly textarea. Story 2.1 §AC4
 * uses it for the three free-form intérêts fields. Caller controls
 * `rows`, `maxLength`, `aria-label`, and any onChange logic.
 */
export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "flex w-full rounded-md border border-border bg-bg px-3 py-2 text-body",
        "placeholder:italic placeholder:text-text-subtle",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-60",
        "resize-y",
        className,
      )}
      {...props}
    />
  );
});
