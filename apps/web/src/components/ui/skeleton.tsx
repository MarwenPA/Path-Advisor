import { cn } from "@/lib/utils";

/**
 * `<Skeleton>` — shadcn-style loading placeholder. Story 2.1 §AC5 uses it
 * during the initial `GET /onboarding/passions` fetch (< 500 ms target).
 * Animation collapses under the global `prefers-reduced-motion` reset in
 * `tokens.css`.
 */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-md bg-bg-2", className)}
      {...props}
    />
  );
}
