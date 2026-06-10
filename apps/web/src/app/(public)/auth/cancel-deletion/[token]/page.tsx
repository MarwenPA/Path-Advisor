import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CancelDeletionForm } from "./cancel-deletion-form";
import {
  type AccountDeletionPublicStatus,
  getPublicAccountDeletionStatus,
} from "@/lib/api/account-deletion";
import { ApiError } from "@/lib/api/client";

export const metadata: Metadata = {
  title: "Annuler la suppression de mon compte | Path-Advisor",
  description:
    "Annule ta demande de suppression de compte Path-Advisor en saisissant ton mot de passe.",
  robots: { index: false, follow: false },
};

interface PageProps {
  params: Promise<{ token: string }>;
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function CancelDeletionPage({ params }: PageProps) {
  const { token } = await params;

  let status: AccountDeletionPublicStatus;
  try {
    status = await getPublicAccountDeletionStatus(token);
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 404) {
      notFound();
    }
    throw cause;
  }

  // Already resolved — show informative copy instead of the form.
  if (status.status === "cancelled") {
    return (
      <main className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-12">
        <h1 className="text-h1 font-semibold text-text">Cette demande a déjà été annulée</h1>
        <p className="text-body text-text-muted">
          Ton compte est restauré. Tu peux te reconnecter normalement.
        </p>
      </main>
    );
  }

  if (status.status === "hard_deleted" || status.status === "expired") {
    return (
      <main className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-12">
        <h1 className="text-h1 font-semibold text-text">Trop tard pour annuler</h1>
        <p className="text-body text-text-muted">
          La fenêtre de 30 jours est dépassée et la suppression a déjà eu lieu ou va survenir
          incessamment. Tu peux créer un nouveau compte à tout moment si tu le souhaites.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text">Annuler la suppression de ton compte</h1>
        <p className="text-body text-text-muted">
          Compte : <strong>{status.user_email_masked}</strong>
        </p>
        <p className="text-body-sm text-text-muted">
          Suppression prévue le <strong>{formatDateTime(status.hard_delete_after)}</strong>.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-bg-2 p-4 text-body-sm text-text-muted">
        Pour confirmer que c&apos;est bien toi, on a besoin de ton mot de passe actuel. Si tu
        l&apos;as oublié, contacte <a href="mailto:dpo@path-advisor.fr">dpo@path-advisor.fr</a>.
      </section>

      <CancelDeletionForm token={token} />
    </main>
  );
}
