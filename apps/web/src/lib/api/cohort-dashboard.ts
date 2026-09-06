/**
 * API client for the counselor cohort dashboard — Story 6.6.
 */
import { apiFetch } from "@/lib/api/client";

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
