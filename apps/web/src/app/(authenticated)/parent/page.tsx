/**
 * /parent — Story 6.2 §T5.3.
 *
 * Parent landing page: lists the children the authenticated parent is actively
 * linked to, each linking to their dashboard. Server Component (fetches on the
 * server, forwarding the session cookie via `apiFetch`). Role is already
 * enforced by the `(authenticated)` layout + `ROUTE_ALLOWED_ROLES["/parent"]`.
 */
import Link from "next/link";

import { fetchLinkedChildren, type LinkedChild } from "@/lib/api/parent";
import { PARENT_COPY } from "@/lib/i18n/fr/parent";

export default async function ParentHomePage() {
  let children: LinkedChild[] = [];
  try {
    children = await fetchLinkedChildren();
  } catch {
    children = [];
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8">
      <h1 className="text-h1 font-bold text-text">{PARENT_COPY.pageTitle}</h1>
      <p className="mt-2 text-body text-text-muted">{PARENT_COPY.pageDescription}</p>

      <h2 className="mb-3 mt-8 text-h2 font-semibold text-text">{PARENT_COPY.childrenListTitle}</h2>

      {children.length === 0 ? (
        <p className="text-body text-text-muted">{PARENT_COPY.childrenEmptyState}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {children.map((child) => (
            <li
              key={child.id}
              className="flex items-center justify-between gap-2 rounded-lg border border-border bg-card p-4"
            >
              <div>
                <p className="text-body font-medium text-text">{child.first_name}</p>
                <span className="text-body-sm text-text-muted">{child.masked_email}</span>
              </div>
              <Link
                href={`/parent/enfants/${encodeURIComponent(child.id)}`}
                className="text-body-sm text-brand underline underline-offset-2"
              >
                {PARENT_COPY.viewDashboardLabel}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
