import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * /auth/forbidden — Story 1.7 §AC8, §AC11.
 *
 * Reached when the `(authenticated)` layout's RBAC guard refuses the user's
 * role for a given path. The `from` query param shows the attempted path
 * (sanitized — `sanitizeNextParam` already ran when the redirect was issued).
 */
export const metadata: Metadata = {
  title: "Accès refusé | Path-Advisor",
  description:
    "Ton compte n'a pas accès à cette page. Contacte ton administrateur si tu penses que c'est une erreur.",
  robots: { index: false, follow: false },
};

interface PageProps {
  searchParams: Promise<{ from?: string }>;
}

export default async function ForbiddenPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const from = params.from ?? null;

  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-bg px-4 py-12">
      <section className="w-full max-w-md space-y-6 text-center">
        <header className="space-y-2">
          <p className="text-text-error text-h1 font-semibold md:text-h1-desktop">403</p>
          <h1 className="text-h2">Accès refusé</h1>
        </header>

        <p className="text-body text-text-muted">
          Ton compte n&apos;a pas l&apos;autorisation d&apos;accéder à cette page. Si tu penses
          qu&apos;il s&apos;agit d&apos;une erreur, contacte ton administrateur (ou le DPO à{" "}
          <a className="underline" href="mailto:dpo@path-advisor.fr">
            dpo@path-advisor.fr
          </a>
          ).
        </p>

        {from && (
          <p className="text-xs text-text-muted">
            Page demandée : <code className="font-mono">{from}</code>
          </p>
        )}

        <div className="flex justify-center gap-3">
          <Button asChild>
            <Link href="/">Retour à l&apos;accueil</Link>
          </Button>
          <Button asChild variant="ghost">
            <Link href="/auth/login">Se reconnecter</Link>
          </Button>
        </div>
      </section>
    </main>
  );
}
