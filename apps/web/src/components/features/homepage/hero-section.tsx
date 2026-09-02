import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * Landing page hero — Story 7.8 §AC1.
 *
 * Owns the page's single `<h1>`. Two primary CTAs route to the existing
 * signup / login flows (Story 1.3/1.5) — no new auth surface introduced.
 */
export function HeroSection() {
  return (
    <section className="flex flex-col items-center gap-6 bg-bg px-4 py-16 text-center md:py-24">
      <h1 className="max-w-2xl text-display-1 font-semibold text-text md:text-display-1-desktop">
        Trouve ta voie, étape par étape.
      </h1>
      <p className="max-w-xl text-body text-text-muted">
        Path-Advisor t&apos;aide à découvrir les métiers qui te correspondent, à comprendre tes
        vraies chances d&apos;admission et à construire ton parcours d&apos;orientation — du collège
        aux études supérieures.
      </p>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button asChild size="lg">
          <Link href="/auth/signup">Créer un compte</Link>
        </Button>
        <Button asChild variant="outline" size="lg">
          <Link href="/auth/login">Se connecter</Link>
        </Button>
      </div>
    </section>
  );
}
