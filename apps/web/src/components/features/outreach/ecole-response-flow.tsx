"use client";

/**
 * <EcoleResponseFlow> — Story 5.12.
 *
 * Generic component composing what `/ecole/outreach/[id]` (Stories 5.6 +
 * 5.7) had built inline: header, "profil scolaire" section, "motivation"
 * section, "métier & parcours visés" section, and the 3-action footer
 * (`<EcoleRespondForm>`) or the read-only response summary once answered.
 *
 * §2 scope decisions — the epic's own prop list (`studentProfile` with
 * moyennes/spés/appréciations, a compatibility score) assumes data that
 * doesn't exist anywhere in this codebase (the `User` model has no name,
 * no grades/spécialités synthesis, and no student↔school compatibility
 * score has ever been built — see Story 5.6 §2 for the same finding).
 * This component renders what the backend actually has: age (not name),
 * no score line (omitted rather than faked).
 *
 * RBAC AC — the privacy reminder ("Tu vois uniquement ce que l'élève a
 * choisi de partager avec toi") is rendered unconditionally; there is no
 * other-schools/other-recos data to accidentally show in the first place
 * (structural, per Story 5.4/5.6's own scope decisions).
 *
 * Layout AC — `lg:grid-cols-2` (profil gauche, actions droite) on desktop
 * (1024px = Tailwind's `lg` breakpoint), single column below. Keyboard
 * shortcuts (i/n/e) live in `<EcoleRespondForm>` itself (§2 — the actions
 * it owns, not duplicated here).
 */
import { EcoleRespondForm } from "./ecole-respond-form";

export interface EcoleResponseFlowProfile {
  id: string;
  student_age: number | null;
  profession_name: string;
  parcours_label: string | null;
  motivation_text: string;
  status: string;
  created_at: string;
  response: {
    action: string;
    comment: string;
    accepted_slot: string;
    alternative_note: string;
  } | null;
}

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  responded: "Répondu",
  expired_7d: "Expiré",
};

const ACTION_LABELS: Record<string, string> = {
  interested: "Profil intéressant",
  not_aligned: "Profil non aligné",
  interview_requested: "Demande d'entretien",
};

export function EcoleResponseFlow({ outreach }: { outreach: EcoleResponseFlowProfile }) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="flex flex-col gap-4">
        {/* Header — âge + date d'envoi. Pas de nom (aucun sur le modèle
            User) ni de score de compatibilité (n'existe nulle part). */}
        <header>
          <p className="text-body text-text">
            {outreach.student_age !== null ? `${outreach.student_age} ans` : "Âge non renseigné"}
          </p>
          <p className="text-caption text-text-subtle">
            Envoyé le{" "}
            {new Date(outreach.created_at).toLocaleDateString("fr-FR", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>
        </header>

        <section aria-label="Profil scolaire" className="rounded-lg border border-border p-4">
          <h3 className="mb-1 text-body-sm font-medium text-text">Profil scolaire</h3>
          <p className="text-body-sm text-text-muted">
            {outreach.student_age !== null ? `${outreach.student_age} ans` : "Non renseigné"}
          </p>
        </section>

        {outreach.motivation_text ? (
          <section aria-label="Motivation" className="rounded-lg border border-border p-4">
            <h3 className="mb-1 text-body-sm font-medium text-text">Motivation</h3>
            <p className="whitespace-pre-wrap text-body-sm text-text-muted">
              {outreach.motivation_text}
            </p>
          </section>
        ) : null}

        <section
          aria-label="Métier et parcours visés"
          className="rounded-lg border border-border p-4"
        >
          <h3 className="mb-1 text-body-sm font-medium text-text">Métier &amp; parcours visés</h3>
          <p className="text-body-sm text-text-muted">{outreach.profession_name}</p>
          {outreach.parcours_label ? (
            <p className="text-body-sm text-text-muted">{outreach.parcours_label}</p>
          ) : null}
        </section>

        <p className="text-caption italic text-text-subtle">
          Tu vois uniquement ce que l&apos;élève a choisi de partager avec toi.
        </p>
      </div>

      <div>
        {outreach.status === "pending" ? (
          <EcoleRespondForm outreachId={outreach.id} />
        ) : outreach.response ? (
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="font-medium text-text">
              Réponse envoyée :{" "}
              {ACTION_LABELS[outreach.response.action] ?? outreach.response.action}
            </p>
            {outreach.response.comment ? (
              <p className="mt-1 text-body-sm text-text-muted">{outreach.response.comment}</p>
            ) : null}
            {outreach.response.action === "interview_requested" ? (
              <p className="mt-2 text-body-sm text-text-muted">
                {outreach.response.accepted_slot
                  ? `Créneau accepté : ${new Date(outreach.response.accepted_slot).toLocaleString("fr-FR")}`
                  : outreach.response.alternative_note
                    ? `L'élève propose : ${outreach.response.alternative_note}`
                    : "En attente de la réponse de l'élève."}
              </p>
            ) : null}
          </div>
        ) : (
          <p className="text-body-sm text-text-muted">
            {STATUS_LABELS[outreach.status] ?? outreach.status}
          </p>
        )}
      </div>
    </div>
  );
}
