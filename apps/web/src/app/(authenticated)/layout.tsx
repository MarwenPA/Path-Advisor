import { LimitedModeBanner } from "@/components/features/auth/limited-mode-banner";
import { MfaBanner } from "@/components/features/auth/mfa-banner";

/**
 * Authenticated route group layout — wraps every page under `/(authenticated)/*`.
 *
 * Renders the LimitedModeBanner once at the top of the tree (Story 1.4 §AC7)
 * and the MfaBanner for staff users who have not enrolled MFA yet
 * (Story 1.6 §AC8 / code-review D6). Both banners self-hide for users they
 * don't apply to so unaffected accounts see the layout unchanged.
 */
export default function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <MfaBanner />
      <LimitedModeBanner />
      {children}
    </div>
  );
}
