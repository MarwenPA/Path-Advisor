import { useTranslations } from "next-intl";
import Link from "next/link";

/**
 * Reassurance / trust section — Story 7.8 §AC2.
 *
 * RGPD confidentiality + "free to start" messaging, with a link to the
 * legal RGPD page (Story 1.x — `/legal/rgpd`).
 *
 * Story 7.7 — strings moved to `messages/fr.json#homepage.trust`. Split
 * into `descriptionBeforeLink` + `privacyLink` rather than one `t.rich()`
 * blob so the `<Link>` stays a real Next.js component (client-side nav),
 * not markup reconstructed from a translated string.
 */
export function TrustSection() {
  const t = useTranslations("homepage.trust");

  return (
    <section aria-labelledby="trust-heading" className="bg-bg-2 px-4 py-16 text-center">
      <h2 id="trust-heading" className="text-h2 font-semibold text-text md:text-h2-desktop">
        {t("title")}
      </h2>
      <p className="mx-auto mt-4 max-w-2xl text-body-sm text-text-muted">
        {t("descriptionBeforeLink")}{" "}
        <Link href="/legal/rgpd" className="underline underline-offset-4 hover:text-text">
          {t("privacyLink")}
        </Link>
        .
      </p>
    </section>
  );
}
