"use client";
import Link from "next/link";
import { MiniGraph } from "./MiniGraph";
import { CarteAdmission } from "@/components/schools/CarteAdmission";
import type { Parcours } from "./types";

interface ParcoursCardProps {
  parcours: Parcours;
  metiersSlug: string;
  onCapture?: (parcoursId: string) => void;
}

export function ParcoursCard({
  parcours,
  metiersSlug: _metiersSlug,
  onCapture,
}: ParcoursCardProps) {
  const targetNode = parcours.nodes.find((n) => n.type === "target");
  const admissionStat = targetNode?.admission_stat ?? null;

  return (
    <article
      className="space-y-3 rounded-xl border bg-card p-4"
      aria-label={"Parcours vers " + (parcours.target_school_name ?? "ecole cible")}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium">{parcours.target_school_name ?? "Ecole cible"}</p>
          {parcours.niveau_scolaire && (
            <span className="text-xs text-muted-foreground">{parcours.niveau_scolaire}</span>
          )}
        </div>
        {admissionStat && (
          <CarteAdmission
            admissionStat={admissionStat}
            variant="small"
            schoolName={parcours.target_school_name ?? ""}
          />
        )}
      </div>

      <MiniGraph nodes={parcours.nodes} edges={parcours.edges} />

      <div className="flex items-center justify-between gap-2 pt-1">
        <Link
          href={"/schools/" + (parcours.target_school_slug ?? parcours.target_school)}
          className="text-xs text-brand underline"
        >
          Voir la fiche
        </Link>
        {onCapture && (
          <button
            type="button"
            onClick={() => onCapture(parcours.id)}
            className="rounded-lg border px-3 py-1 text-xs"
            aria-label={"Capturer ce parcours vers " + (parcours.target_school_name ?? "l ecole")}
          >
            Capturer
          </button>
        )}
      </div>
    </article>
  );
}
