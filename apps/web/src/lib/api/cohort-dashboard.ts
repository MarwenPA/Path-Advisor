/**
 * API client for the counselor cohort dashboard — Story 6.6.
 */
import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface CohortDashboardKpis {
  nb_eleves: number;
  taux_completion_profil: number;
  nb_eleves_mode_degrade: number;
}

export interface CohortDashboardTopMetier {
  name: string;
  count: number;
}

export interface CohortDashboardFiliere {
  filiere: string;
  count: number;
}

export interface CohortDashboardActivity {
  student_id: string;
  derniere_connexion: string;
}

export interface CohortDashboardEleve {
  student_id: string;
  cohort_name: string;
}

export interface CohortDashboard {
  kpis: CohortDashboardKpis;
  top_metiers: CohortDashboardTopMetier[];
  distribution_filiere: CohortDashboardFiliere[];
  activite_recente: CohortDashboardActivity[];
  eleves: CohortDashboardEleve[];
}

export async function fetchCohortDashboard(): Promise<CohortDashboard> {
  return apiFetch<CohortDashboard>("/api/v1/establishments/cohort-dashboard/");
}

/** Story 6.9 AC — CSV export URL (a plain link, not a fetch: the browser
 * handles the file download via Content-Disposition, same pattern as
 * `ECOLE_REPORTING_EXPORT_URL`). Aggregate-only, k-anonymized — never
 * contains a student id or name. */
export const COHORT_REPORTING_EXPORT_URL = "/api/v1/establishments/cohort-dashboard/export.csv/";

// --- Story 10.1 — profils à risque ------------------------------------------

export type AtRiskReasonCode = "faible_engagement" | "profil_incoherent" | "baisse_moyenne";

export interface AtRiskReason {
  code: AtRiskReasonCode;
  days_inactive?: number;
  nb_passions?: number;
  drop?: number;
  from_average?: number;
  to_average?: number;
}

export interface AtRiskStudent {
  student_id: string;
  cohort_name: string;
  reasons: AtRiskReason[];
  consent_granted: boolean;
  intervention_in_progress: boolean;
}

export interface AtRiskResponse {
  students: AtRiskStudent[];
  /** Élèves évalués sur le seul signal d'activité (consentement 6.7 absent). */
  students_without_consent: number;
}

export async function fetchAtRiskStudents(): Promise<AtRiskResponse> {
  return apiFetch<AtRiskResponse>("/api/v1/establishments/cohort-dashboard/at-risk/");
}

export async function markIntervention(studentId: string): Promise<void> {
  await apiFetch(`/api/v1/establishments/students/${encodeURIComponent(studentId)}/intervention/`, {
    method: "POST",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}

export async function resolveIntervention(studentId: string): Promise<void> {
  await apiFetch(`/api/v1/establishments/students/${encodeURIComponent(studentId)}/intervention/`, {
    method: "DELETE",
    csrfToken: readCsrfCookie() ?? undefined,
  });
}
