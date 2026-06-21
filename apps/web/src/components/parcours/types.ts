// Parcours types — Story 4.3 / 4.5 / 4.6 / 4.7

export interface AdmissionStatInline {
  expected_proba: number;
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
  context_line?: string;
  action_lever?: string | null;
}

export interface ParcoursNode {
  id: string;
  label: string;
  /** "start" | "intermediate" | "target" | "diplome" | "ecole" | "stage" | "concours" */
  type: string;
  schoolId?: string;
  schoolSlug?: string;
  duration_label?: string;
  /** Inline admission stat injected by the backend (Story 4.5 AC2). */
  admission_stat?: AdmissionStatInline | null;
}

export interface ParcoursEdge {
  source: string;
  target: string;
  weight?: number;
}

/**
 * Parcours item returned by GET /api/v1/metiers/{slug}/parcours/
 *
 * Story 4.3 base fields + Story 4.5 nodes_with_stats + Story 4.6 target school metadata
 * for client-side filtering + Story 4.7 label and admission date fields.
 */
export interface Parcours {
  id: string;
  profession: string;
  target_school: string | null;
  target_school_name: string | null;
  target_school_slug: string | null;
  target_school_city: string | null;
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
  nodes_with_stats?: ParcoursNode[];
  niveau_scolaire: string;
  is_default: boolean;
  // Story 4.7
  label: string;
  updated_at?: string;
  created_at?: string;
  target_school_affelnet_dates: Record<string, string> | null;
  target_school_parcoursup_dates: Record<string, string> | null;
  // Story 4.6 filter metadata
  target_school_tuition_max: number | null;
  target_school_selectivity: number | null;
  target_school_apprenticeship: boolean | null;
  target_school_internship: boolean | null;
}
