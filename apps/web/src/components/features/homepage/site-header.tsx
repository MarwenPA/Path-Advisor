import { useTranslations } from "next-intl";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { LogoWordmark } from "@/components/ui/logo";

export function SiteHeader() {
  const t = useTranslations("homepage.header");

  return (
    <header className="border-b border-border bg-bg">
      <div className="mx-auto flex min-h-16 max-w-5xl items-center justify-between gap-4 px-4">
        <Link href="/" aria-label={t("homeLinkLabel")} className="inline-flex items-center">
          <LogoWordmark className="gap-2.5" />
        </Link>
        <Button asChild variant="outline" size="sm">
          <Link href="/auth/login">{t("loginCta")}</Link>
        </Button>
      </div>
    </header>
  );
}
