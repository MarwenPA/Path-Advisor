"use client";

import type { School, Formation } from "@/lib/api/schools";
import { cn } from "@/lib/utils";
import { CarteAdmission } from "./CarteAdmission";

interface FicheEcoleProps {
  school: School;
  variant?: "card" | "expanded";
  className?: string;
}

function SelectivityStars({ index }: { index: number }) {
  return (
    <div aria-label={`Sélectivité : ${index} sur 5`} className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={cn("text-sm", i <= index ? "text-amber-500" : "text-gray-200")}>
          ★
        </span>
      ))}
    </div>
  );
}

function FormationItem({ formation }: { formation: Formation }) {
  return (
    <li className="flex items-center justify-between py-1.5 text-sm">
      <span>{formation.name}</span>
      <span className="text-muted-foreground">
        {formation.duration_years} an{formation.duration_years > 1 ? "s" : ""}
      </span>
    </li>
  );
}

export function FicheEcole({ school, variant = "card", className }: FicheEcoleProps) {
  return (
    <article
      aria-label={`Fiche de ${school.name}`}
      className={cn("rounded-xl border bg-card", variant === "expanded" ? "p-6" : "p-4", className)}
    >
      {/* Header */}
      <div className="mb-3">
        <h2 className="text-lg font-semibold">{school.name}</h2>
        <p className="text-sm text-muted-foreground">
          {school.city} · {school.region}
        </p>
      </div>

      {/* Key info as dl */}
      <dl className="mb-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
        <dt className="text-muted-foreground">Type</dt>
        <dd>{school.type}</dd>

        <dt className="text-muted-foreground">Accès</dt>
        <dd>{school.public_private}</dd>

        <dt className="text-muted-foreground">Sélectivité</dt>
        <dd>
          <SelectivityStars index={school.selectivity_index} />
        </dd>

        {school.tuition_min_eur !== undefined && school.tuition_max_eur !== undefined && (
          <>
            <dt className="text-muted-foreground">Frais</dt>
            <dd>
              {school.tuition_min_eur === 0 && school.tuition_max_eur === 0
                ? "Gratuit"
                : `${school.tuition_min_eur}–${school.tuition_max_eur} €/an`}
            </dd>
          </>
        )}

        {school.apprenticeship && (
          <>
            <dt className="text-muted-foreground">Alternance</dt>
            <dd>Disponible</dd>
          </>
        )}
      </dl>

      {/* Formations list — only in expanded variant */}
      {variant === "expanded" && school.formations.length > 0 && (
        <section aria-label="Formations disponibles">
          <h3 className="mb-1 text-sm font-medium">Formations</h3>
          <ul className="divide-y">
            {school.formations.map((f) => (
              <FormationItem key={f.id} formation={f} />
            ))}
          </ul>
        </section>
      )}

      {/* Débouchés — only in expanded variant */}
      {variant === "expanded" && school.top_debouches.length > 0 && (
        <section aria-label="Débouchés principaux" className="mt-3">
          <h3 className="mb-1 text-sm font-medium">Débouchés</h3>
          <ul className="flex flex-wrap gap-1.5">
            {school.top_debouches.map((d) => (
              <li key={d} className="rounded-full bg-muted px-2.5 py-0.5 text-xs">
                {d}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Statistique d'admission — only in expanded variant (Story 4.5 AC1, AC5) */}
      {variant === "expanded" && (
        <section aria-label="Statistique d'admission" className="mt-4">
          <h3 className="mb-2 text-sm font-medium">Tes chances d&apos;admission</h3>
          {school.admission_stat ? (
            <CarteAdmission
              admissionStat={school.admission_stat}
              variant="medium"
              schoolName={school.name}
              schoolSlug={school.slug}
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              Donn&eacute;es d&apos;admission non disponibles
            </p>
          )}
        </section>
      )}
    </article>
  );
}
