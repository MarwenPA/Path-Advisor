// Parcours types — Story 4.3

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
}
