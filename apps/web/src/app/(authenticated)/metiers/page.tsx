/**
 * `/metiers` — catalogue complet des métiers du référentiel. Story 3.13.
 *
 * Repli quand `/accueil`'s "Tes métiers" n'a pas encore de recommandations
 * scorées (profil pas assez rempli) — l'élève peut quand même parcourir
 * tout le référentiel (52 métiers seedés au lancement de cette story,
 * `apps/professions/management/commands/seed_professions.py`). Chaque
 * carte renvoie vers la fiche détail existante `/metiers/{slug}` (Story
 * 3.5/3.12, inchangée).
 *
 * "Image" par métier (2026-09-05, demandé explicitement) : le référentiel
 * `Profession` n'a aucun champ photo (scraping/enrichissement du
 * référentiel reporté à une story dédiée future — voir `deferred-work.md`).
 * En attendant de vraies photos, chaque carte affiche une icône de secteur
 * (`SECTOR_ICONS`) dans un badge coloré — un vrai visuel plutôt qu'un bloc
 * de texte nu, sans dépendre d'assets externes qui pourraient casser.
 *
 * Server Component — un seul fetch, pas de pagination client pour l'instant
 * (52 métiers tiennent dans une page ; `fetchProfessions` prend un `page`
 * en prévision de la croissance du référentiel, story de scraping future).
 */
import {
  Briefcase,
  FlaskConical,
  GraduationCap,
  HardHat,
  HeartPulse,
  Landmark,
  Leaf,
  Palette,
  Shield,
  Truck,
  Users,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { fetchProfessions, type ProfessionCatalogItem } from "@/lib/api/professions";

export const metadata = { title: "Tous les métiers — Path Advisor" };

/** One icon + one accent color per `sector` — falls back to a generic
 * briefcase/neutral pairing for an unknown or empty sector. */
const SECTOR_VISUALS: Record<string, { icon: LucideIcon; className: string }> = {
  santé: { icon: HeartPulse, className: "bg-danger/10 text-danger" },
  tech: { icon: Landmark, className: "bg-semantic-sur/10 text-semantic-sur" },
  btp: { icon: HardHat, className: "bg-warning/10 text-warning" },
  business: { icon: Briefcase, className: "bg-semantic-realiste/10 text-semantic-realiste" },
  arts: { icon: Palette, className: "bg-brand/10 text-brand" },
  enseignement: { icon: GraduationCap, className: "bg-semantic-sur/10 text-semantic-sur" },
  environnement: { icon: Leaf, className: "bg-success/10 text-success" },
  industrie: { icon: HardHat, className: "bg-semantic-audacieux/10 text-semantic-audacieux" },
  sciences: { icon: FlaskConical, className: "bg-semantic-sur/10 text-semantic-sur" },
  securite: { icon: Shield, className: "bg-danger/10 text-danger" },
  social: { icon: Users, className: "bg-semantic-realiste/10 text-semantic-realiste" },
  transport: { icon: Truck, className: "bg-semantic-audacieux/10 text-semantic-audacieux" },
};

const FALLBACK_VISUAL = { icon: Briefcase, className: "bg-muted text-muted-foreground" };

function SectorBadge({ sector }: { sector?: string }) {
  const { icon: Icon, className } = (sector && SECTOR_VISUALS[sector]) || FALLBACK_VISUAL;
  return (
    <span
      aria-hidden="true"
      className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${className}`}
    >
      <Icon className="h-7 w-7" />
    </span>
  );
}

function ProfessionCard({ profession }: { profession: ProfessionCatalogItem }) {
  return (
    <Link href={`/metiers/${profession.slug}`} className="block h-full">
      <Card className="h-full transition-colors hover:border-brand">
        <CardHeader className="flex-row items-start gap-4 space-y-0">
          <SectorBadge sector={profession.sector} />
          <div className="min-w-0 flex-1">
            <h2 className="text-h3 font-semibold text-text">{profession.name}</h2>
            {profession.sector && (
              <span className="text-caption uppercase tracking-wide text-text-subtle">
                {profession.sector}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <p className="line-clamp-3 text-body-sm text-text-muted">{profession.description}</p>
          {profession.median_salary_eur ? (
            <p className="mt-2 text-body-sm font-medium text-text">
              ~{profession.median_salary_eur.toLocaleString("fr-FR")} € / an
            </p>
          ) : null}
        </CardContent>
      </Card>
    </Link>
  );
}

export default async function MetiersCataloguePage() {
  const { results: professions } = await fetchProfessions();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold">Tous les métiers</h1>
      <p className="mb-6 text-body text-text-muted">
        {professions.length} métiers à explorer, en attendant tes recommandations personnalisées.
      </p>

      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {professions.map((p) => (
          <li key={p.id}>
            <ProfessionCard profession={p} />
          </li>
        ))}
      </ul>
    </main>
  );
}
