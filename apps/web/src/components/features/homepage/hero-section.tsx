import { Check } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { Button } from "@/components/ui/button";

import { RecommendationExample } from "./recommendation-example";

const GUARANTEE_IDS = ["free", "neutral", "explained"] as const;

/**
 * Landing page hero — Story 7.8 §AC1.
 *
 * Owns the page's single `<h1>`. Two primary CTAs route to the existing
 * signup / login flows (Story 1.3/1.5) — no new auth surface introduced.
 */
export function HeroSection() {
  const t = useTranslations("homepage.hero");

  return (
    <section className="bg-bg px-4 py-16 md:py-24">
      <div className="mx-auto grid max-w-5xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:gap-14">
        <div>
          <p className="inline-flex items-center gap-2 text-caption font-semibold uppercase tracking-[0.08em] text-brand before:h-0.5 before:w-5 before:bg-brand">
            {t("eyebrow")}
          </p>
          <h1 className="mt-4 max-w-2xl text-display-1 font-semibold text-text md:text-display-1-desktop">
            {t("titleLead")} <span className="text-brand">{t("titleAccent")}</span>
          </h1>
          <p className="mt-5 max-w-xl text-body text-text-muted">{t("subtitle")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/auth/signup">{t("signupCta")}</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/auth/login">{t("loginCta")}</Link>
            </Button>
          </div>
          <ul
            aria-label={t("guaranteesLabel")}
            className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-body-sm text-text-subtle"
          >
            {GUARANTEE_IDS.map((id) => (
              <li key={id} className="inline-flex items-center gap-1.5">
                <Check className="size-3.5 text-success" aria-hidden="true" />
                {t(`guarantees.${id}`)}
              </li>
            ))}
          </ul>
        </div>
        <RecommendationExample />
      </div>
    </section>
  );
}
