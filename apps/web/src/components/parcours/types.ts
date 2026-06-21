// Parcours types — Story 4.3 / 4.6

export interface ParcoursNode {
  id: string;
  label: string;
  /** "start" | "intermediate" | "target" | "diplome" | "ecole" | "stage" | "concours" */
  type: string;
  schoolId?: string;
  schoolSlug?: string;
  duration_label?: string;
}

export interface ParcoursEdge {
  source: string;
  target: string;
  weight?: number;
}

export interface AdmissionStatInline {
  expected_proba: number;
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
}

/**
 * Parcours item returned by GET /api/v1/metiers/{slug}/parcours/
 * Story 4.3 base fields + Story 4.6 target school metadata for client-side filtering.
 */
export interface Parcours {
  id: string;
  profession: string;
  target_school: string;
  target_school_name?: string;
  target_school_slug?: string;
  target_school_city?: string;
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
  niveau_scolaire: string;
  is_default: boolean;
  created_at?: string;
  // Story 4.6 filter metadata
  target_school_tuition_max: number | null;
  target_school_selectivity: number;
  target_school_apprenticeship: boolean;
  target_school_internship: boolean;
}
