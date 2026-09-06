import { useTranslations } from "next-intl";
import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * Landing page hero — Story 7.8 §AC1.
 *
 * Owns the page's single `<h1>`. Two primary CTAs route to the existing
 * signup / login flows (Story 1.3/1.5) — no new auth surface introduced.
 *
 * Story 7.7 — strings moved to `messages/fr.json#homepage.hero`.
 */
export function HeroSection() {
  const t = useTranslations("homepage.hero");

  return (
    <section className="flex flex-col items-center gap-6 bg-bg px-4 py-16 text-center md:py-24">
      <h1 className="max-w-2xl text-display-1 font-semibold text-text md:text-display-1-desktop">
        {t("title")}
      </h1>
      <p className="max-w-xl text-body text-text-muted">{t("subtitle")}</p>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button asChild size="lg">
          <Link href="/auth/signup">{t("signupCta")}</Link>
        </Button>
        <Button asChild variant="outline" size="lg">
          <Link href="/auth/login">{t("loginCta")}</Link>
        </Button>
      </div>
    </section>
  );
}
