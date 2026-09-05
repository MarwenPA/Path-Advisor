import { redirect } from "next/navigation";

/**
 * `/onboarding` — Story 1.3 shipped this as a static "coming soon"
 * placeholder pending the real flow (Story 2.1). That flow shipped
 * (`/onboarding/step-1` → `step-2` → `step-3`, each a real, working page —
 * `step-1`'s own docstring already assumes it's "the entry point"), but this
 * index page was never updated to match: every route that lands here
 * (`(public)/auth/verify-email/page.tsx`'s post-verification redirect,
 * anyone navigating to `/onboarding` directly) hit the stale placeholder
 * and got told the feature "arrive avec Story 2.1" — permanently, since
 * nothing else ever redirected onward.
 *
 * Code-review fix (2026-09): redirect straight to the real entry point.
 * `step-1` itself already handles the "already completed step 1" case
 * (redirects onward to `step-2`), so this is the correct single entry
 * point for both a fresh signup and someone returning mid-flow.
 */
export default function OnboardingPage() {
  redirect("/onboarding/step-1");
}
