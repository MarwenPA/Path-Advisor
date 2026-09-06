/**
 * /parent/enfants/[studentId] — Story 6.2 §T5.4 / AC1.
 *
 * Renders the dashboard for one linked child. Server Component: fetches the
 * dashboard (forwarding the session cookie) then hands the data to the
 * `ParentDashboard` client component. A 403 (parent not linked to this child,
 * AC4) redirects to the forbidden page — the backend is the authority.
 */
import { redirect } from "next/navigation";

import { ChildSubscriptionSection } from "@/components/features/parent/child-subscription-section";
import { ParentDashboard } from "@/components/features/parent/parent-dashboard";
import { ApiError } from "@/lib/api/client";
import { fetchChildDashboard, type ParentChildDashboard } from "@/lib/api/parent";
import { PARENT_COPY } from "@/lib/i18n/fr/parent";

export const dynamic = "force-dynamic";

export default async function ParentChildDashboardPage({
  params,
}: {
  params: Promise<{ studentId: string }>;
}) {
  const { studentId } = await params;

  let dashboard: ParentChildDashboard;
  try {
    dashboard = await fetchChildDashboard(studentId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 403) {
      redirect(`/auth/forbidden?from=/parent/enfants/${encodeURIComponent(studentId)}`);
    }
    throw err;
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8">
      <h1 className="text-h1 font-bold text-text">
        {PARENT_COPY.pageTitle} — {dashboard.child.first_name}
      </h1>
      <p className="mt-2 text-body text-text-muted">{dashboard.child.masked_email}</p>
      <div className="mt-6">
        <ChildSubscriptionSection studentId={studentId} />
      </div>
      <div className="mt-8">
        <ParentDashboard dashboard={dashboard} studentId={studentId} />
      </div>
    </main>
  );
}
