"use client";

/**
 * "Nécessite ton attention" — Story 10.1 (FR-FF1).
 *
 * Wording constructif par construction (AC3) : la section s'appelle
 * « Nécessite ton attention », jamais « élèves en échec » ; chaque motif est
 * une phrase d'accompagnement, pas un verdict. Les CODES viennent de l'API
 * (`risk_detection.py`), la copie vit ici — côté conseillère uniquement,
 * l'élève n'a aucune surface pour ce signal.
 *
 * Deux groupes : les alertes actives d'abord, puis « intervention en
 * cours » (marquées pour éviter les doublons — AC2). Le marquage est
 * optimiste avec retour arrière en cas d'échec, comme les toggles 8.2.
 *
 * Français en dur comme le reste de l'UI cohorte (dette i18n préexistante
 * du namespace cohorte, consignée — non aggravée ici).
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import type { AtRiskReason, AtRiskResponse, AtRiskStudent } from "@/lib/api/cohort-dashboard";
import { markIntervention, resolveIntervention } from "@/lib/api/cohort-dashboard";

function reasonLabel(reason: AtRiskReason): string {
  switch (reason.code) {
    case "faible_engagement":
      return `Pas de connexion depuis ${reason.days_inactive} jours — un message peut relancer l'exploration.`;
    case "profil_incoherent":
      return "Ses passions et ses spécialités ne se recoupent pas — un échange pourrait l'aider à y voir clair.";
    case "baisse_moyenne":
      return `Sa moyenne est passée de ${reason.from_average} à ${reason.to_average} — un entretien permettrait de comprendre ce qui change.`;
  }
}

export function AtRiskPanel({ initial }: { initial: AtRiskResponse }) {
  const router = useRouter();
  const [students, setStudents] = useState<AtRiskStudent[]>(initial.students);
  const [error, setError] = useState(false);

  const setInProgress = (studentId: string, value: boolean) => {
    setStudents((prev) =>
      prev.map((s) => (s.student_id === studentId ? { ...s, intervention_in_progress: value } : s)),
    );
  };

  const handleToggle = async (student: AtRiskStudent) => {
    const next = !student.intervention_in_progress;
    setError(false);
    setInProgress(student.student_id, next); // optimiste
    try {
      if (next) {
        await markIntervention(student.student_id);
      } else {
        await resolveIntervention(student.student_id);
      }
    } catch {
      setInProgress(student.student_id, !next); // retour arrière
      setError(true);
    }
  };

  const alerting = students.filter((s) => !s.intervention_in_progress);
  const inProgress = students.filter((s) => s.intervention_in_progress);

  if (students.length === 0 && initial.students_without_consent === 0) return null;

  const renderStudent = (student: AtRiskStudent) => (
    <li
      key={student.student_id}
      className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="font-mono text-body-sm text-text">{student.student_id}</span>
        <span className="text-body-sm text-text-muted">{student.cohort_name}</span>
      </div>
      <ul className="flex flex-col gap-1">
        {student.reasons.map((reason) => (
          <li key={reason.code} className="text-body-sm text-text">
            {reasonLabel(reason)}
          </li>
        ))}
      </ul>
      {!student.consent_granted && (
        <p className="text-body-sm text-text-muted">
          Sans consentement, seule l&apos;activité est évaluée — demande le consentement pour une
          vue complète.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => router.push(`/cohorte/eleves/${student.student_id}`)}
          className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-bg-2"
        >
          Suggérer un entretien — voir le profil
        </button>
        <button
          type="button"
          onClick={() => void handleToggle(student)}
          className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-bg-2"
        >
          {student.intervention_in_progress
            ? "Intervention terminée"
            : "Marquer l'intervention en cours"}
        </button>
      </div>
    </li>
  );

  return (
    <section aria-labelledby="at-risk-title" className="mb-6 flex flex-col gap-3">
      <h2 id="at-risk-title" className="text-lg font-semibold text-text">
        Nécessite ton attention
      </h2>
      {error && (
        <p role="alert" className="text-body-sm text-danger">
          Le marquage n&apos;a pas pu être enregistré — l&apos;état a été remis comme avant.
        </p>
      )}
      {initial.students_without_consent > 0 && (
        <p className="text-body-sm text-text-muted">
          {initial.students_without_consent} élève(s) sans consentement : seuls les signaux
          d&apos;activité sont évalués pour eux.
        </p>
      )}
      {alerting.length === 0 ? (
        <p className="text-body-sm text-text-muted">
          Aucun profil ne demande ton attention en ce moment.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">{alerting.map(renderStudent)}</ul>
      )}
      {inProgress.length > 0 && (
        <>
          <h3 className="text-body font-medium text-text">Intervention en cours</h3>
          <ul className="flex flex-col gap-3">{inProgress.map(renderStudent)}</ul>
        </>
      )}
    </section>
  );
}
