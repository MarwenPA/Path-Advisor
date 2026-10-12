import { ListChecks, Scale, ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * Reassurance / trust section — Story 7.8 §AC2.
 *
 * RGPD confidentiality + "free to start" messaging, with a link to the
 * legal RGPD page (Story 1.x — `/legal/rgpd`).
 */
const POINTS = [
  { id: "hosting", Icon: ShieldCheck },
  { id: "neutrality", Icon: Scale },
  { id: "explainability", Icon: ListChecks },
] as const;

export function TrustSection() {
  const t = useTranslations("homepage.trust");
  const tHero = useTranslations("homepage.hero");

  return (
    <section aria-labelledby="trust-heading" className="bg-bg-2 px-4 py-16">
      <div className="mx-auto grid max-w-5xl items-start gap-8 lg:grid-cols-2 lg:gap-14">
        <div>
          <h2 id="trust-heading" className="text-h2 font-semibold text-text md:text-h2-desktop">
            {t("title")}
          </h2>
          <p className="mt-2.5 max-w-2xl text-body text-text-muted">{t("description")}</p>
          <ul className="mt-6 grid gap-3.5">
            {POINTS.map(({ id, Icon }) => (
              <li key={id} className="grid grid-cols-[20px_1fr] gap-3 text-body-sm text-text-muted">
                <Icon className="mt-0.5 size-5 text-success" aria-hidden="true" />
                <span>
                  <strong className="block font-semibold text-text">
                    {t(`points.${id}.title`)}
                  </strong>
                  {t(`points.${id}.description`)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="grid content-start gap-3.5 rounded-lg border border-border bg-bg p-7">
          <h3 className="text-h3 font-semibold text-text md:text-h3-desktop">{t("cta.title")}</h3>
          <p className="text-body-sm text-text-muted">{t("cta.description")}</p>
          <div className="mt-1 flex flex-wrap gap-2.5">
            <Button asChild size="lg">
              <Link href="/auth/signup">{tHero("signupCta")}</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/auth/login">{tHero("loginCta")}</Link>
            </Button>
          </div>
          <Link
            href="/legal/rgpd"
            className="text-body-sm text-text-subtle underline underline-offset-4 hover:text-text"
          >
            {t("privacyLink")}
          </Link>
        </div>
      </div>
    </section>
  );
}
