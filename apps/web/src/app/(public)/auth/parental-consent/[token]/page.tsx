import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ParentalConsentFlow } from "@/components/features/auth/parental-consent-flow";
import type { ParentalConsentStatus } from "@/lib/api/auth";

export const metadata: Metadata = {
  title: "Autoriser l'inscription | Path-Advisor",
  // No-auth tokenized URL — keep search engines out.
  robots: { index: false, follow: false },
};

// Always render fresh per request — the token state can change between two clicks
// (parent re-opens the email after a grant); we never want a stale "pending" view.
export const dynamic = "force-dynamic";

async function fetchInitialStatus(token: string): Promise<ParentalConsentStatus | null> {
  // Server-side fetch — the API runs on `pa-api:8000` inside docker; we hit it
  // through the host port from the Next.js Node runtime.
  const apiBase = process.env.API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(
      `${apiBase}/api/v1/auth/parental-consent/${encodeURIComponent(token)}/`,
      {
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
    if (!res.ok) return null;
    return (await res.json()) as ParentalConsentStatus;
  } catch {
    return null;
  }
}

export default async function ParentalConsentPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const status = await fetchInitialStatus(token);

  if (!status) notFound();

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 px-4 py-12">
      <header className="flex flex-col gap-2">
        <p className="text-body-sm uppercase tracking-wide text-text-muted">
          Autorisation parentale
        </p>
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">
          Path-Advisor a besoin de votre autorisation pour que votre enfant utilise le service.
        </h1>
        <p className="text-body text-text-muted">
          Compte concerné&nbsp;:{" "}
          <strong className="font-medium text-text">{status.student_email_masked}</strong>
          {" — "}âge déclaré&nbsp;:{" "}
          <strong className="font-medium text-text">{status.child_age} ans</strong>
        </p>
      </header>

      <section
        aria-labelledby="explainer-title"
        className="grid gap-6 rounded-md border border-border bg-bg-2 p-6 md:grid-cols-3"
      >
        <h2 id="explainer-title" className="sr-only">
          À propos de Path-Advisor
        </h2>
        <article className="flex flex-col gap-2">
          <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">Ce que c&apos;est</h3>
          <p className="text-body-sm text-text-muted">
            Un service français qui aide les jeunes à explorer des métiers et des parcours adaptés à
            leur profil, sans pression et avec une transparence totale sur les recommandations.
          </p>
        </article>
        <article className="flex flex-col gap-2">
          <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">Données collectées</h3>
          <p className="text-body-sm text-text-muted">
            Email + mot de passe chiffré, profil scolaire (saisi ou OCR de bulletins), interactions
            avec le service. Tout reste en France.
          </p>
        </article>
        <article className="flex flex-col gap-2">
          <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">Vos droits</h3>
          <p className="text-body-sm text-text-muted">
            Vous pouvez autoriser, refuser ou révoquer à tout moment. Toute question&nbsp;:{" "}
            <a href="mailto:dpo@path-advisor.fr" className="text-brand underline">
              dpo@path-advisor.fr
            </a>
            .
          </p>
        </article>
      </section>

      <ParentalConsentFlow token={token} initial={status} />
    </main>
  );
}
