export interface ParcoursNode {
  id: string;
  label: string;
  type: "start" | "intermediate" | "target";
  schoolId?: string;
  schoolSlug?: string;
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
 * Extended in Story 4.6 with target school metadata used for client-side filtering.
 */
export interface Parcours {
  id: string;
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
  target_school_name: string;
  target_school_tuition_max: number | null;
  target_school_selectivity: number;
  target_school_apprenticeship: boolean;
  target_school_internship: boolean;
}
