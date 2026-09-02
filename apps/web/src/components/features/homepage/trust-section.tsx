import Link from "next/link";

/**
 * Reassurance / trust section — Story 7.8 §AC2.
 *
 * RGPD confidentiality + "free to start" messaging, with a link to the
 * legal RGPD page (Story 1.x — `/legal/rgpd`).
 */
export function TrustSection() {
  return (
    <section aria-labelledby="trust-heading" className="bg-bg-2 px-4 py-16 text-center">
      <h2 id="trust-heading" className="text-h2 font-semibold text-text md:text-h2-desktop">
        Gratuit pour commencer, tes données t&apos;appartiennent
      </h2>
      <p className="mx-auto mt-4 max-w-2xl text-body-sm text-text-muted">
        Créer ton profil et découvrir tes premières recommandations est gratuit. Path-Advisor est
        conçu dans le respect du RGPD : tu gardes le contrôle sur tes données à tout moment.{" "}
        <Link href="/legal/rgpd" className="underline underline-offset-4 hover:text-text">
          En savoir plus sur la confidentialité
        </Link>
        .
      </p>
    </section>
  );
}
