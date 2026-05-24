import { LimitedModeBanner } from "@/components/features/auth/limited-mode-banner";

/**
 * Authenticated route group layout — wraps every page under `/(authenticated)/*`.
 *
 * Renders the LimitedModeBanner once at the top of the tree (Story 1.4 §AC7). The
 * banner self-hides for fully-active users so authenticated layouts for adult
 * accounts are visually identical to their pre-1.4 rendering.
 */
export default function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <LimitedModeBanner />
      {children}
    </div>
  );
}
