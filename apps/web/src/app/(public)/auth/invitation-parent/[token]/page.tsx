import type { Metadata } from "next";

import { ParentSignupForm } from "@/components/features/family/parent-signup-form";
import { PARENT_SIGNUP_COPY } from "@/lib/i18n/fr/family";
import type { ParentInvitationPublicStatus } from "@/lib/api/family";

export const metadata: Metadata = {
  title: "Rejoindre Path-Advisor | Path-Advisor",
  robots: { index: false, follow: false },
};

// Story 1.4 §T6 pattern — always render fresh, the token state can change
// between two clicks (e.g. accepted then re-opened).
export const dynamic = "force-dynamic";

async function fetchInvitationStatus(token: string): Promise<ParentInvitationPublicStatus | null> {
  const apiBase = process.env.API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(
      `${apiBase}/api/v1/family/parent-invitations/${encodeURIComponent(token)}/`,
      { cache: "no-store", headers: { Accept: "application/json" } },
    );
    if (!res.ok) return null;
    return (await res.json()) as ParentInvitationPublicStatus;
  } catch {
    return null;
  }
}

export default async function InvitationParentPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const status = await fetchInvitationStatus(token);

  if (!status || status.status !== "pending") {
    return (
      <main className="mx-auto flex w-full max-w-lg flex-col gap-4 px-4 py-16 text-center">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          {PARENT_SIGNUP_COPY.invalidLinkTitle}
        </h1>
        <p className="text-body text-text-muted">{PARENT_SIGNUP_COPY.invalidLinkDescription}</p>
        <a href="mailto:support@path-advisor.fr" className="text-brand underline">
          {PARENT_SIGNUP_COPY.contactSupportLabel}
        </a>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <p className="text-body-sm uppercase tracking-wide text-text-muted">
          Invitation de {status.student_first_name}
        </p>
        {status.custom_message ? (
          <p className="text-body italic text-text-muted">« {status.custom_message} »</p>
        ) : null}
      </header>
      <ParentSignupForm token={token} prefillEmail={status.parent_email} />
    </main>
  );
}
