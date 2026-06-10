import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Compte désactivé | Path-Advisor",
  description:
    "Ta demande de suppression de compte Path-Advisor a été prise en compte. Tu as 30 jours pour annuler via le lien envoyé par email.",
  robots: { index: false, follow: false },
};

export default function AccountDeletedPage() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text">Ton compte est désactivé</h1>
        <p className="text-body text-text-muted">
          On a bien pris en compte ta demande de suppression. Tu as <strong>30 jours</strong> pour
          changer d&apos;avis.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-bg-2 p-4 text-body">
        <p>
          Un email avec un lien d&apos;annulation t&apos;a été envoyé. Si tu ne le reçois pas dans
          les prochaines minutes, vérifie tes spams.
        </p>
        <p className="mt-3 text-body-sm text-text-muted">
          Passé les 30 jours, tes données seront effacées définitivement (sauf le journal
          d&apos;audit pseudonymisé, conservé 3 ans pour des raisons légales).
        </p>
      </section>

      <p className="text-body-sm text-text-muted">
        Tu n&apos;as pas demandé cette suppression ?{" "}
        <a href="mailto:dpo@path-advisor.fr" className="text-brand underline">
          Contacte le DPO immédiatement.
        </a>
      </p>

      <p>
        <Link href="/" className="text-brand underline">
          ← Retour à l&apos;accueil
        </Link>
      </p>
    </main>
  );
}
